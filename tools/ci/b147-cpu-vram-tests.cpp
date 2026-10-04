#include "shader-hash-memo.h"
#include "frame-costs.h"
#include "checkpoint-content.h"
#include "vram-pressure.h"
#include <memory>
#include <thread>
#include <cstdio>
#include <cstdlib>
static void Check(bool b) {if(!b)std::abort();}
struct MockImage {
 bool registered=true,depth_id=false,gpu=false,stencil=false,buffer=false;
 struct {bool texture=true,storage=false,render_target=false,depth_target=false,video_out=false;} usage;
 struct {bool depth=false,stencil=false;struct {int kind=0;} metadata;bool IsDepth() const{return depth;}bool HasStencil()const{return stencil;}} info;
 bool IsGpuModified()const{return gpu;}bool IsStencilModified()const{return stencil;}bool IsBufferModified()const{return buffer;}
};
int main() {
 auto c=std::make_unique<ShaderHashMemo::Cache>();unsigned calls=0;uint64_t value=41;
 auto hash=[&]{++calls;return value;};
 Check(c->Get(0x1000,128,1,false,hash)==41);
 for(int i=0;i<63;++i)Check(c->Get(0x1000,128,1,false,hash)==41);
 Check(calls==1);value=42;
 Check(c->Get(0x1000,128,1,false,hash)==42 && calls==2);
 value=43;Check(c->Get(0x1000,128,1,false,hash)==43 && calls==3); // unstable code never memoized again
 Check(c->Get(0x1000,128,2,false,hash)==43 && calls==4); // registration invalidation
 value=44;Check(c->Get(0x1000,132,2,false,hash)==44 && calls==5); // size invalidation
 value=45;Check(c->Get(0x1000,132,2,true,hash)==45 && calls==6); // verify checks every use
 c=std::make_unique<ShaderHashMemo::Cache>();value=47;Check(c->Get(0x1000,128,1,false,hash)==47);
 uint64_t collision=0x1100;while((((collision>>8)^(collision>>20))&8191)!=16)collision+=256;
 value=48;Check(c->Get(collision,128,1,false,hash)==48);
 value=49;Check(c->Get(0x1000,128,1,false,hash)==49); // direct-map collision invalidated the original entry
 std::thread t([]{auto other=std::make_unique<ShaderHashMemo::Cache>();Check(other->Get(0x1000,128,1,false,[]{return 99;})==99);});t.join();
 FrameCosts::Ledger l;auto root=l.Enter(FrameCosts::Translation,100);auto child=l.Enter(FrameCosts::GpuWait,150);l.Leave(child,250);l.Leave(root,300);
 Check(l.ns[FrameCosts::Translation]==100 && l.ns[FrameCosts::GpuWait]==100 && l.active==-1);
 root=l.Enter(FrameCosts::Texture,400);l.Charge(450);l.ns.fill(0);l.Leave(root,500);Check(l.ns[FrameCosts::Texture]==50); // report inside live scope
 CheckpointContent cp;Check(!cp.Matches(1,100,true));cp.Saved(1,100);Check(cp.Matches(1,100,true));
 Check(!cp.Matches(1,101,true)&&!cp.Matches(2,100,true)&&!cp.Matches(1,100,false)); // changed/missing checkpoint retry
 constexpr uint64_t G=1ull<<30;
 Check(!VramPressure::Reclaim(0,0));Check(VramPressure::Target(256ull<<20)==240ull<<20);
 Check(VramPressure::Reclaim(7*G,7*G));Check(!VramPressure::Reclaim(4*G,7*G));
 Check(VramPressure::PoolLimit(8*G,7*G,G,G)==0);Check(VramPressure::PoolLimit(G,7*G,G,G)==G);
 Check(VramPressure::PoolLimit(0,0,G,G)==0); // no unsigned underflow
 MockImage image;Check(VramPressure::CpuBackedSampled(image,0));
 auto unsafe=[&](auto member){image=MockImage{};image.*member=true;Check(!VramPressure::CpuBackedSampled(image,0));};
 unsafe(&MockImage::gpu);unsafe(&MockImage::stencil);unsafe(&MockImage::buffer);unsafe(&MockImage::depth_id);
 image=MockImage{};image.info.depth=true;Check(!VramPressure::CpuBackedSampled(image,0));
 image=MockImage{};image.info.stencil=true;Check(!VramPressure::CpuBackedSampled(image,0));
 image=MockImage{};image.info.metadata.kind=1;Check(!VramPressure::CpuBackedSampled(image,0));
 image=MockImage{};image.usage.storage=true;Check(!VramPressure::CpuBackedSampled(image,0));
 image=MockImage{};image.usage.render_target=true;Check(!VramPressure::CpuBackedSampled(image,0));
 image=MockImage{};image.usage.depth_target=true;Check(!VramPressure::CpuBackedSampled(image,0));
 image=MockImage{};image.usage.video_out=true;Check(!VramPressure::CpuBackedSampled(image,0));
 image=MockImage{};image.usage.texture=false;Check(!VramPressure::CpuBackedSampled(image,0));
 image=MockImage{};image.registered=false;Check(!VramPressure::CpuBackedSampled(image,0));
 std::puts("B147 hash invalidation, exclusive accounting, checkpoint retry and CPU-backed pressure safety passed");
}
