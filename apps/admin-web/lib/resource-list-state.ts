export type ResourceListState = "loading" | "initial-empty" | "populated" | "filtered-empty";

export function resolveResourceListState(totalRecords: number | undefined, visibleRecords: number | undefined, filtered: boolean): ResourceListState {
  if (totalRecords === undefined || visibleRecords === undefined) return "loading";
  if (totalRecords === 0) return "initial-empty";
  if (filtered && visibleRecords === 0) return "filtered-empty";
  return "populated";
}
