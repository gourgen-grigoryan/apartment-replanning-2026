using System;
using System.Collections.Generic;
using System.Drawing;
using System.Drawing.Imaging;
using System.Globalization;
using System.IO;
using System.Runtime.InteropServices;
using System.Threading.Tasks;

// Ray-traced views of the same triangulation used by the IFC exporter.
// Usage: Render.exe <mesh directory> <output directory> [width] [samples per pixel]
public static class Render
{
    struct V {
        public double x,y,z;
        public V(double a,double b,double c){x=a;y=b;z=c;}
        public static V operator +(V a,V b){return new V(a.x+b.x,a.y+b.y,a.z+b.z);}
        public static V operator -(V a,V b){return new V(a.x-b.x,a.y-b.y,a.z-b.z);}
        public static V operator *(V a,double b){return new V(a.x*b,a.y*b,a.z*b);}
        public static V operator *(V a,V b){return new V(a.x*b.x,a.y*b.y,a.z*b.z);}
        public double Dot(V b){return x*b.x+y*b.y+z*b.z;}
        public V Cross(V b){return new V(y*b.z-z*b.y,z*b.x-x*b.z,x*b.y-y*b.x);}
        public V Unit(){return this*(1/Math.Sqrt(Dot(this)));}
        public double At(int i){return i==0?x:i==1?y:z;}
        public static V Min(V a,V b){return new V(Math.Min(a.x,b.x),Math.Min(a.y,b.y),Math.Min(a.z,b.z));}
        public static V Max(V a,V b){return new V(Math.Max(a.x,b.x),Math.Max(a.y,b.y),Math.Max(a.z,b.z));}
    }
    class Tri {public V a,e,f,n,min,max,mid;public int mat,group;}
    class Node {public V min,max;public Node l,r;public int first,last;}
    struct Ray {
        public V o,d,inv;
        public Ray(V pos,V dir){o=pos;d=dir;inv=new V(1/(dir.x+1e-24),1/(dir.y+1e-24),1/(dir.z+1e-24));}
    }
    static Tri[] triangles;
    static Node tree;
    static V[] palette, lights;
    static double[] luminousFlux, lightHeight;
    static bool cut, outside;
    static readonly V white=new V(1,1,1), up=new V(0,0,1);
    static Node Build(int first,int last){
        Node n=new Node{first=first,last=last,min=white*1e8,max=white*(-1e8)};
        for(int i=first;i<last;i++){n.min=V.Min(n.min,triangles[i].min);n.max=V.Max(n.max,triangles[i].max);}
        if(last-first<=8)return n;
        V e=n.max-n.min;int axis=e.x>e.y&&e.x>e.z?0:e.y>e.z?1:2;
        Array.Sort(triangles,first,last-first,Comparer<Tri>.Create((a,b)=>a.mid.At(axis).CompareTo(b.mid.At(axis))));
        int mid=(first+last)/2;n.l=Build(first,mid);n.r=Build(mid,last);return n;
    }
    static bool Box(Ray r,Node n,double lim){
        V v=(n.min-r.o)*r.inv,w=(n.max-r.o)*r.inv;
        V lo=V.Min(v,w),hi=V.Max(v,w);
        return Math.Max(0,Math.Max(lo.x,Math.Max(lo.y,lo.z)))<=Math.Min(lim,Math.Min(hi.x,Math.Min(hi.y,hi.z)));
    }
    static bool Hit(Node n,Ray r,ref double t,ref Tri hit,bool skipGlass,bool any){
        if(!Box(r,n,t))return false;
        if(n.l!=null){bool h=Hit(n.l,r,ref t,ref hit,skipGlass,any);if(h&&any)return true;return Hit(n.r,r,ref t,ref hit,skipGlass,any)||h;}
        bool found=false;
        for(int i=n.first;i<n.last;i++){
            Tri a=triangles[i];
            if((skipGlass&&a.mat==13)||(cut&&a.group==1))continue;
            V p=r.d.Cross(a.f);double det=a.e.Dot(p);if(Math.Abs(det)<1e-11)continue;
            V v=r.o-a.a;double u=v.Dot(p)/det;if(u<0||u>1)continue;
            V q=v.Cross(a.e);double b=r.d.Dot(q)/det;if(b<0||u+b>1)continue;
            double d=a.f.Dot(q)/det;if(d<.0005 || d>t)continue;
            double z=r.o.z+d*r.d.z;
            if(cut&&((a.group==2||a.group==3)&&z>1.12||a.group==5&&z>2.0))continue;
            hit=a;t=d;found=true;if(any)return true;
        }return found;
    }
    static double Rand(ref uint s){s^=s<<13;s^=s>>17;s^=s<<5;return (s+.5)/4294967296.0;}
    static double Frac(double x){return x-Math.Floor(x);}
    static V Texture(int m,V p,V n){
        V color=palette[m];double u=Math.Abs(n.x)>.7?p.y:p.x,v=Math.Abs(n.z)>.7?p.y:p.z;
        if(m==2||m==3||m==4){
            double row=Math.Floor(v/.145),offset=Math.Sin(row*82.13)*1.42;
            double seam=m==4&&(Frac(v/.145)<.012||Frac((u+offset)/1.74)<.0017)?.76:1;
            double grain=.038*Math.Sin(840*v+2.8*Math.Sin(6*u+13*v))+.021*Math.Sin(144*v+1.6*Math.Sin(1.8*u))+.018*Math.Sin(523*v);
            return color*(seam*(.985+grain+.045*Math.Sin(row*51.2)));
        }
        if(m==5||m==21){double line=Math.Min(Math.Min(Frac(u/.6),1-Frac(u/.6)),Math.Min(Frac(v/.6),1-Frac(v/.6)));return color*(line<.003?.77:.985+.018*Math.Sin(16*u+1.4*Math.Sin(11*v)));}
        if(m==6||m==7||m==8)return color*(.984+.015*Math.Sin(850*u)*Math.Sin(860*v));
        return color;
    }
    static V Sky(V dir){
        double z=Math.Min(1,Math.Max(0,dir.z));
        if(cut)return new V(.79,.83,.80);
        if(dir.z<0)return new V(.58,.63,.58)*(1+.24*dir.z);
        return new V(.94,1.02,1.09)*(1-z)+new V(.39,.60,.81)*z;
    }
    static bool Blocked(V p,V u,double dist){
        Tri tr=null;return Hit(tree,new Ray(p,u),ref dist,ref tr,true,true);
    }
    static V Shade(Ray ray,ref uint seed,int depth,bool skipGlass){
        double dist=1e4;Tri tri=null;
        if(!Hit(tree,ray,ref dist,ref tri,skipGlass,false))return Sky(ray.d);
        V p=ray.o+ray.d*dist,n=tri.n;if(n.Dot(ray.d)>0)n=n*(-1);
        V start=p+n*.0021;
        if(tri.mat==13){
            V refl=ray.d-n*(2*ray.d.Dot(n));double f=.038+.38*Math.Pow(1+ray.d.Dot(n),5);
            return Shade(new Ray(p+ray.d*.003,ray.d),ref seed,depth+1,true)*new V(.953,.984,.978)*(1-f)+Sky(refl)*f;
        }
        if(tri.mat==15)return new V(2.8,2.29,1.65);
        V tx=Texture(tri.mat,p,n);
        V tangent=(Math.Abs(n.z)<.85?up.Cross(n):new V(1,0,0).Cross(n)).Unit(),bit=n.Cross(tangent);
        double rr=Math.Sqrt(Rand(ref seed)),ang=Rand(ref seed)*2*Math.PI;
        V ao=tangent*(rr*Math.Cos(ang))+bit*(rr*Math.Sin(ang))+n*Math.Sqrt(1-rr*rr);
        double reach=.85;Tri oc=null;bool occ=Hit(tree,new Ray(start,ao),ref reach,ref oc,true,false);
        double ambient=(outside?.68:.53)*(occ?.58+.42*reach/.85:1)*(.87+.13*n.z);
        V illum=new V(.98,.97,.94)*ambient;
        V win=new V(Math.Max(.35,Math.Min(8.45,p.x))+(Rand(ref seed)-.5)*1.4,8.93,1.6+Rand(ref seed)*2.2)-p;
        double wd=Math.Sqrt(win.Dot(win));V wu=win*(1/wd);double cosine=n.Dot(wu);
        if(cosine>0&&!Blocked(start,wu,wd-.1))illum+=new V(.86,.95,1.03)*(cosine*1.2);
        V sun=new V(-.29,.77,.57).Unit();cosine=n.Dot(sun);
        if(cosine>0&&!Blocked(start,sun,35))illum+=new V(1.0,.90,.72)*(cosine*.63);
        if(!cut&&!outside){
            for(int j=0;j<lights.Length;j++){
                V delta=lights[j]-p;double squared=delta.Dot(delta);if(squared>25)continue;
                delta+=new V((Rand(ref seed)-.5)*.045,(Rand(ref seed)-.5)*.045,-lightHeight[j]*.5-.013);
                double ld=Math.Sqrt(delta.Dot(delta));V u=delta*(1/ld);cosine=n.Dot(u);
                double falloff=Math.Max(0,1-squared/25);
                if(cosine>0&&!Blocked(start,u,ld-.025))illum+=new V(1,.89,.75)*(cosine*falloff*luminousFlux[j]/(1000+700*squared));
            }
        }
        V result=tx*illum;
        double shine=tri.mat==14?.79:tri.mat==10?.18:tri.mat==12?.07:0;
        if(shine>0&&depth<1){
            V refl=ray.d-n*(2*ray.d.Dot(n));result=result*(1-shine)+Shade(new Ray(start,refl),ref seed,depth+1,true)*shine;
        }return result;
    }
    static int Byte(double a){return (int)(255*Math.Pow(Math.Max(0,Math.Min(1,(a*1.12)/(1+.18*a))),1/2.2)+.00001);}
    static V ReadV(BinaryReader b){return new V(b.ReadSingle(),b.ReadSingle(),b.ReadSingle());}
    static V ReadV(string[] s,int i){return new V(Parse(s[i]),Parse(s[i+1]),Parse(s[i+2]));}
    static double Parse(string s){return double.Parse(s,CultureInfo.InvariantCulture);}
    public static void Main(string[] args){
        string work=args[0],dest=args[1];int width=args.Length>2?int.Parse(args[2]):1080,spp=args.Length>3?int.Parse(args[3]):4,height=width*2/3;
        string[] hex="e8e2d3 859484 bd926a 936849 bb956e b8b7a9 9b6854 eee5ce 818979 353a3b aeb7b8 d9d4c5 edece3 b5d7d4 a8bcbf fff1c9 acaaa0 7199af bd745e 649aaf bc9a60 859286".Split(' ');
        palette=Array.ConvertAll(hex,s=>{Color c=ColorTranslator.FromHtml("#"+s);return new V(Math.Pow(c.R/255.0,2.2),Math.Pow(c.G/255.0,2.2),Math.Pow(c.B/255.0,2.2));});
        string[][] sourceLights=Array.ConvertAll(File.ReadAllLines(Path.Combine(work,"lights.txt")),s=>s.Split(' '));
        lights=Array.ConvertAll(sourceLights,s=>ReadV(s,0));luminousFlux=Array.ConvertAll(sourceLights,s=>Parse(s[3]));lightHeight=Array.ConvertAll(sourceLights,s=>Parse(s[4]));
        var list=new List<Tri>();
        using(var br=new BinaryReader(File.OpenRead(Path.Combine(work,"triangles.dat")))){
            while(br.BaseStream.Position<br.BaseStream.Length){V a=ReadV(br),b=ReadV(br),c=ReadV(br);V e=b-a,f=c-a;list.Add(new Tri{a=a,e=e,f=f,n=e.Cross(f).Unit(),mid=(a+b+c)*(1.0/3),min=V.Min(a,V.Min(b,c)),max=V.Max(a,V.Max(b,c)),mat=(int)br.ReadSingle(),group=(int)br.ReadSingle()});}
        }
        triangles=list.ToArray();tree=Build(0,triangles.Length);Directory.CreateDirectory(dest);
        foreach(string row in File.ReadAllLines(Path.Combine(work,"cameras.txt"))){
            string[] s=row.Split(' ');V eye=ReadV(s,1),forward=(ReadV(s,4)-eye).Unit(),right=forward.Cross(up).Unit(),vertical=right.Cross(forward);
            cut=s[0].Contains("cutaway");outside=cut||s[0].Contains("facade");
            double scale=Math.Tan(Parse(s[7])*Math.PI/360);int stride=(width*3+3)&~3;byte[] pixels=new byte[stride*height];
            Parallel.For(0,height,y=>{for(int x=0;x<width;x++){
                uint seed=(uint)((x+1)*73856093^(y+1)*19349663)|1;V sum=new V(0,0,0);
                for(int j=0;j<spp;j++){
                    double dx=(2*(x+(j+Rand(ref seed))/spp)/width-1)*scale,dy=(height-2*(y+Rand(ref seed)))/width*scale;
                    sum+=Shade(new Ray(eye,(forward+right*dx+vertical*dy).Unit()),ref seed,0,false);
                }
                sum=sum*(1.0/spp);int i=y*stride+3*x;pixels[i]=(byte)Byte(sum.z);pixels[i+1]=(byte)Byte(sum.y);pixels[i+2]=(byte)Byte(sum.x);
            }});
            // Remove isolated Monte Carlo noise while preserving visible edges.
            byte[] clean=(byte[])pixels.Clone();
            Parallel.For(2,height-2,y=>{for(int x=2;x<width-2;x++){
                int i=stride*y+x*3;double b=0,g=0,r=0,weight=0;
                for(int v=-2;v<=2;v++)for(int u=-2;u<=2;u++){
                    int k=i+v*stride+u*3,db=pixels[k]-pixels[i],dg=pixels[k+1]-pixels[i+1],dr=pixels[k+2]-pixels[i+2];
                    double w=Math.Exp(-(u*u+v*v)/4.5-(db*db+dg*dg+dr*dr)/1152.0);
                    b+=w*pixels[k];g+=w*pixels[k+1];r+=w*pixels[k+2];weight+=w;
                }clean[i]=(byte)(b/weight+.5);clean[i+1]=(byte)(g/weight+.5);clean[i+2]=(byte)(r/weight+.5);
            }});
            using(var bmp=new Bitmap(width,height,PixelFormat.Format24bppRgb)){
                var data=bmp.LockBits(new Rectangle(0,0,width,height),ImageLockMode.WriteOnly,PixelFormat.Format24bppRgb);
                Marshal.Copy(clean,0,data.Scan0,clean.Length);bmp.UnlockBits(data);
                using(var parameters=new EncoderParameters(1)){
                    parameters.Param[0]=new EncoderParameter(System.Drawing.Imaging.Encoder.Quality,94L);
                    var encoder=Array.Find(ImageCodecInfo.GetImageEncoders(),c=>c.FormatID==ImageFormat.Jpeg.Guid);
                    bmp.Save(Path.Combine(dest,s[0]+".jpg"),encoder,parameters);
                }
            }
            Console.WriteLine(s[0]);
        }
    }
}
