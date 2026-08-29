import type { InsightArticle } from "./insights-data";
import type { Locale } from "./home-copy";

const API_URL = process.env.ARE_API_URL ?? process.env.NEXT_PUBLIC_ARE_API_URL ?? "http://127.0.0.1:50003/api/v1";
export const API_ORIGIN = new URL(API_URL).origin;
export type PublicProperty = { id:string;slug:string;purpose:string;property_type:string;emirate:string;community:string;developer:string|null;bedrooms:number|null;bathrooms:number|null;area:string|null;area_unit:string|null;price:string|null;price_on_request:boolean;currency:string;featured:boolean;published_at:string|null;title:string;description:string };
export type PublicJob = { id:string;slug:string;department:string;location:string;employment_type:string;closing_date:string|null;status:string;title:string;description:string;responsibilities:string[];requirements:string[];benefits:string[] };
export type PublicDeveloper = { id:string;slug:string;primary_emirate:string;other_presence:string[];selected_projects:string[];official_website:string;source_url:string;additional_source_urls:string[];verification_date:string;enquiry_types:("new-booking"|"primary-sale"|"resale")[];featured:boolean;display_order:number;status:"published";published_at:string|null;name:string;description:string;focus:string;verification_note:string };
export type ProjectPreviewMedia = { id:string;category:string;thumbnail_url:string;full_url:string;alt:string|null;width:number|null;height:number|null;display_order:number };
export type PublicProject = { id:string;slug:string;emirate:string;developer:{slug:string;name:string};area:{slug:string;name_en:string;name_ar:string;emirate:string};availability_status?:string|null;construction_status?:string|null;handover_quarter?:string|null;handover_year?:number|null;original_handover_value?:string|null;handover_verification?:string;property_types?:string[];bedroom_options?:string[];unit_types?:Array<{label:string;display_order:number}>;size_min?:string|number|null;size_max?:string|number|null;size_unit?:string|null;size_ranges?:Array<{property_type:string;minimum:number;maximum:number}>;down_payment_percentage?:string|number|null;payment_plan?:{is_complete:boolean;milestones:Array<{sequence:number;stage:string;label:string|null;percentage:string|number|null}>}|null;amenities?:Array<{label:string;display_order:number}>;nearby_places?:Array<{name:string;travel_time_minutes:number|null;display_order:number}>;media?:Array<{id:string;category:string;url:string;alt:string|null;width:number|null;height:number|null}>;official_name:string;short_summary:string;full_description:string;cta:string };
export type CandidateProjectPreview = { candidate_id:string;locale:Locale;project_name:string;developer:{name:string};emirate:string;area:string;overview:string|null;property_types?:string[];unit_types?:string[];bedrooms?:string[];size_min?:number|null;size_max?:number|null;size_unit?:string|null;size_ranges?:Array<{property_type:string;minimum:number;maximum:number}>;down_payment_percentage?:number|null;payment_plan?:{raw_source_text?:string;is_complete?:boolean;requires_review?:boolean;milestones:Array<{sequence?:number;stage?:string;label_en?:string|null;label_ar?:string|null;percentage?:number|null}>}|null;payment_milestones?:Array<{sequence:number;stage:string;percentage:number|null}>;handover_quarter?:string|null;handover_year?:number|null;handover_verification?:string;availability_status?:string|null;construction_status?:string|null;amenities?:string[];nearby_places?:Array<{name:string;travel_time_minutes:number|null}>;media?:ProjectPreviewMedia[];has_cover:boolean };
type PublicInsight = { id:string;slug:string;category:InsightArticle["category"];published_at:string|null;updated_at:string;source_links:InsightArticle["sources"];body:InsightArticle["content"][Locale] };
type Page<T> = { items:T[]; meta:{total:number} };

async function get<T>(path:string):Promise<T|null>{
  try { const response=await fetch(`${API_URL}${path}`,{cache:"no-store",signal:AbortSignal.timeout(3500)}); return response.ok ? response.json() as Promise<T> : null; } catch { return null; }
}
export async function getProperties(locale:Locale,query=""){ return (await get<Page<PublicProperty>>(`/public/properties?locale=${locale}&page_size=100${query}`))?.items ?? []; }
export async function getProperty(locale:Locale,slug:string){ return get<PublicProperty>(`/public/properties/${encodeURIComponent(slug)}?locale=${locale}`); }
export async function getJobs(locale:Locale){ return (await get<Page<PublicJob>>(`/public/jobs?locale=${locale}`))?.items ?? []; }
export async function getDevelopers(locale:Locale){ return (await get<Page<PublicDeveloper>>(`/public/developers?locale=${locale}`))?.items ?? null; }
export async function getProjects(locale:Locale){ return (await get<Page<PublicProject>>(`/public/projects?locale=${locale}&page_size=100`))?.items ?? []; }
export async function getProject(locale:Locale,slug:string){ return get<PublicProject>(`/public/projects/${encodeURIComponent(slug)}?locale=${locale}`); }
export async function getCandidateProjectPreview(locale:Locale,batchId:string,candidateId:string,cookie:string){
  try {
    const response=await fetch(`${API_URL}/admin/project-imports/${encodeURIComponent(batchId)}/candidates/${encodeURIComponent(candidateId)}/preview?locale=${locale}`,{
      cache:"no-store",
      headers:{cookie},
      signal:AbortSignal.timeout(3500),
    });
    return response.ok ? response.json() as Promise<CandidateProjectPreview> : null;
  } catch { return null; }
}
export async function getCandidateProjectPreviewMedia(candidateId:string,mediaId:string,size:"thumbnail"|"full",cookie:string){
  try {
    return await fetch(`${API_URL}/admin/project-imports/candidates/${encodeURIComponent(candidateId)}/preview-media/${encodeURIComponent(mediaId)}?size=${size}`,{
      cache:"no-store",
      headers:{cookie},
      signal:AbortSignal.timeout(3500),
    });
  } catch { return null; }
}
export async function getDraftProjectPreview(locale:Locale,projectId:string,cookie:string){
  try {
    const response=await fetch(`${API_URL}/admin/projects/${encodeURIComponent(projectId)}/preview?locale=${locale}`,{
      cache:"no-store",
      headers:{cookie},
      signal:AbortSignal.timeout(3500),
    });
    return response.ok ? response.json() as Promise<PublicProject> : null;
  } catch { return null; }
}
export async function getDraftProjectPreviewMedia(projectId:string,mediaId:string,cookie:string){
  try {
    return await fetch(`${API_URL}/admin/projects/${encodeURIComponent(projectId)}/preview-media/${encodeURIComponent(mediaId)}`,{
      cache:"no-store",
      headers:{cookie},
      signal:AbortSignal.timeout(3500),
    });
  } catch { return null; }
}
export async function getDeveloper(locale:Locale,slug:string){ return get<PublicDeveloper>(`/public/developers/${encodeURIComponent(slug)}?locale=${locale}`); }
export async function getJob(locale:Locale,slug:string){ return get<PublicJob>(`/public/jobs/${encodeURIComponent(slug)}?locale=${locale}`); }
export async function getInsights(locale:Locale){
  const items=(await get<Page<PublicInsight>>(`/public/insights?locale=${locale}&page_size=100`))?.items ?? [];
  return items.map((item):InsightArticle=>({slug:item.slug,category:item.category,published:item.published_at?.slice(0,10)??item.updated_at.slice(0,10),updated:item.updated_at.slice(0,10),sources:item.source_links,content:{en:item.body,ar:item.body}}));
}
export async function getInsight(locale:Locale,slug:string){
  const item=await get<PublicInsight>(`/public/insights/${encodeURIComponent(slug)}?locale=${locale}`);
  return item ? ({slug:item.slug,category:item.category,published:item.published_at?.slice(0,10)??item.updated_at.slice(0,10),updated:item.updated_at.slice(0,10),sources:item.source_links,content:{en:item.body,ar:item.body}} satisfies InsightArticle) : null;
}
