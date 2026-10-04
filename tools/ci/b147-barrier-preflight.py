"""Compile the production image barrier method and descriptor identity gates with CPU mocks."""
import argparse
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
s=(a.source/'src/graphics/host_gpu/renderer/image/image.cpp').read_text()
method=s[s.index('const Image::Barriers& Image::GetBarriers('):s.index('\nvoid BeginTransitGroup()')]
n=(a.source/'src/local/native-xpr.inc').read_text()
gate=n[n.index('const bool same_objects ='):n.index('\n\tif (runtime)',n.index('const bool same_objects ='))]
loop=n[n.index('for (const auto& dep: record.buffers)',n.index('bool RenderExecutor::NativeXprRebindSlots(')):n.index('\n\tstd::array',n.index('for (const auto& dep: record.buffers)',n.index('bool RenderExecutor::NativeXprRebindSlots(')))]
instance=n[n.index('\tstruct Occurrence {'):n.index('\n\t// The latest relocated try:',n.index('\tstruct Occurrence {'))]
a.output.write_text(r'''
#include <algorithm>
#include <array>
#include <cstdint>
#include <vector>
#include <optional>
#include <ranges>
#include <utility>
#include <cstdlib>
#include <cstdio>
#define EXIT_IF(x) do {if(x)std::abort();}while(0)
constexpr uint32_t VK_QUEUE_FAMILY_IGNORED=~0u,VK_REMAINING_MIP_LEVELS=~0u,VK_REMAINING_ARRAY_LAYERS=~0u;
namespace vk {
using AccessFlags2=uint64_t;using PipelineStageFlags2=uint64_t;
enum AccessFlagBits2:uint64_t {eTransferWrite=1,eShaderWrite=2,eMemoryWrite=4,eShaderRead=8,eTransferRead=16};
enum PipelineStageFlagBits2:uint64_t {eAllCommands=1,eAllGraphics=2,eComputeShader=4,eTransfer=8};
enum class ImageLayout {eUndefined,eGeneral,eShaderReadOnlyOptimal,eTransferDstOptimal};
struct ImageMemoryBarrier2 {uint64_t srcStageMask=0,srcAccessMask=0,dstStageMask=0,dstAccessMask=0;
 ImageLayout oldLayout{},newLayout{};uint32_t srcQueueFamilyIndex=0,dstQueueFamilyIndex=0;int image=0;
 struct {uint32_t aspectMask=0,baseMipLevel=0,levelCount=0,baseArrayLayer=0,layerCount=0;}subresourceRange;};
}
struct ImageSubresourceRange {uint32_t base_level=0,level_count=1,base_layer=0,layer_count=1;};
struct State {uint64_t pl_stage=0,access_mask=0;vk::ImageLayout layout=vk::ImageLayout::eUndefined;bool guest=false;};
struct Image {
 using Barriers=std::vector<vk::ImageMemoryBarrier2>;
 struct {State state;std::vector<State>subresource_states;int image=1,format=1;}backing;
 struct {struct{uint32_t levels=1,layers=1;}resources;bool volume=false;bool IsVolume()const{return volume;}}info;
 uint64_t transit_group=0;static uint32_t FullAspectMask(int){return 1;}
 const Barriers& GetBarriers(vk::ImageLayout,vk::AccessFlags2,vk::PipelineStageFlags2,std::optional<ImageSubresourceRange> range=std::nullopt);
};
uint64_t g_transit_group=0;bool reuse=true,dedupe=false;
bool GuestBarrierReuse(){return reuse;}bool DedupeTransitGroups(){return dedupe;}
''' + method + r'''
struct Dep {int id=0,serial=0,stage=0,slot=0,handle=0;};
struct Record {std::vector<Dep>images,buffers;};
bool SameObjects(bool runtime,const Record& record,const std::vector<Dep>& image_deps,const std::vector<Dep>&buffer_deps){
''' + gate + r'''
 return same_objects;
}
struct Owner{int handle;int Handle()const{return handle;}};
struct Buffers{std::vector<Owner>owners;const Owner* GetBufferIfLive(int id)const{return id>=0 && size_t(id)<owners.size()?&owners[id]:nullptr;}};
bool RebindSafe(const Record&record,const std::vector<std::pair<int,int>>&buffer_slots,const Buffers&buffers){
''' + loop + r'''
 return true;
}
struct InstanceCache {static uint64_t IndexHash(uint64_t h){return h!=0?h:1;}
''' + instance + r'''
};
void Check(bool b){if(!b)std::abort();}
int main(){
 using L=vk::ImageLayout;using A=vk::AccessFlagBits2;using S=vk::PipelineStageFlagBits2;
 Image image;g_transit_group=1;
 Check(image.GetBarriers(L::eGeneral,A::eShaderWrite,S::eAllGraphics).size()==1);
 g_transit_group=2;Check(image.GetBarriers(L::eGeneral,A::eShaderWrite,S::eAllGraphics).empty());
 g_transit_group=0;Check(image.GetBarriers(L::eGeneral,A::eShaderWrite,S::eAllGraphics).size()==1); // emulator write
 g_transit_group=3;Check(image.GetBarriers(L::eGeneral,A::eShaderWrite,S::eAllGraphics).size()==1); // external->guest
 Check(image.GetBarriers(L::eGeneral,A::eShaderRead,S::eAllGraphics).size()==1); // write->read preserved
 Check(image.GetBarriers(L::eGeneral,A::eShaderWrite,S::eAllGraphics).size()==1); // read->write preserved
 Check(image.GetBarriers(L::eTransferDstOptimal,A::eTransferWrite,S::eTransfer).size()==1); // layout preserved
 g_transit_group=0;Check(image.GetBarriers(L::eTransferDstOptimal,A::eTransferWrite,S::eTransfer).size()==1); // repeated host transfer
 image=Image{};reuse=false;g_transit_group=1;
 Check(image.GetBarriers(L::eGeneral,A::eShaderWrite,S::eAllGraphics).size()==1);
 g_transit_group=2;Check(image.GetBarriers(L::eGeneral,A::eShaderWrite,S::eAllGraphics).size()==1); // A/B original path
 reuse=true;image=Image{};image.info.resources={2,2};g_transit_group=1;
 auto first=ImageSubresourceRange{0,1,0,1};auto last=ImageSubresourceRange{1,1,1,1};
 Check(image.GetBarriers(L::eGeneral,A::eShaderWrite,S::eAllGraphics,first).size()==1);
 g_transit_group=2;Check(image.GetBarriers(L::eGeneral,A::eShaderWrite,S::eAllGraphics,first).empty());
 Check(image.backing.subresource_states[3].layout==L::eUndefined);
 Check(image.GetBarriers(L::eGeneral,A::eShaderWrite,S::eAllGraphics,last).size()==1);
 g_transit_group=0;Check(image.GetBarriers(L::eGeneral,A::eShaderWrite,S::eAllGraphics,first).size()==1);
 g_transit_group=3;Check(image.GetBarriers(L::eGeneral,A::eShaderWrite,S::eAllGraphics,first).size()==1);
 Check(image.GetBarriers(L::eGeneral,A::eShaderWrite,S::eAllGraphics).size()==2); // untouched mip/layers still transition
 Check(image.backing.subresource_states.empty());
 Record record{{{1,1}},{{1,0,0,0,100}}};
 Check(SameObjects(true,record,record.images,record.buffers));auto deps=record.buffers;deps[0].id=2;
 Check(!SameObjects(true,record,record.images,deps)); // identical descriptor bytes, recycled buffer owner
 auto images=record.images;images[0].serial=2;Check(!SameObjects(true,record,images,record.buffers));
 Buffers buffers{{{0},{100}}};Check(RebindSafe(record,{},buffers));buffers.owners[1].handle=101;Check(!RebindSafe(record,{},buffers));
 buffers.owners.clear();Check(!RebindSafe(record,{},buffers));Check(RebindSafe(record,{{0,0}},buffers)); // changed slot is re-resolved
 InstanceCache instances;Check(!instances.Rebound(123));instances.MarkRebound(123);Check(instances.Rebound(123));
 Check(instances.NextOccurrence(111,1)==0 && instances.NextOccurrence(222,1)==0);
 Check(instances.NextOccurrence(111,1)==1);
 Check(instances.NextOccurrence(222,2)==0 && instances.NextOccurrence(111,2)==0); // reorder keeps each identity's first occurrence
 Check(instances.NextOccurrence(222,3)==0); // other instance culled
 Check(instances.NextOccurrence(111,4)==0 && instances.NextOccurrence(222,4)==0); // instance returns
 for(uint64_t i=0;i<16;++i)Check(instances.NextOccurrence(1000+i*8192,5)==0);
 Check(instances.NextOccurrence(1000+16*8192,5)==UINT32_MAX); // bounded collision fallback
 std::puts("B147 production barrier transitions and native descriptor lifetime gates passed");
}
''')
