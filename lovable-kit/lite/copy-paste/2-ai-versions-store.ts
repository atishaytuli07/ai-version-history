// ai-versions (Lite): the only file that talks to the database.
// The version pill finds this file automatically and switches to database mode.
// Keep these two function names and return values exactly as they are.
import { supabase } from "@/integrations/supabase/client";

export type AiVersionRow = {
  version: string;
  entry_hash: string;
  level: string;
  summary: string;
  note: string;
  reason: string;
  restored_from: string | null;
  created_at?: string | null;
};

// Every version, in any order.
export async function listAiVersions(): Promise<AiVersionRow[]> {
  const { data, error } = await supabase.from("ai_versions").select("*");
  if (error) throw error;
  return (data ?? []) as AiVersionRow[];
}

// Adds one version. "duplicate" means that number was just taken by another preview.
export async function addAiVersion(row: AiVersionRow): Promise<"ok" | "duplicate"> {
  const { created_at: _ignored, ...insert } = row;
  const { error } = await supabase.from("ai_versions").insert(insert);
  if (!error) return "ok";
  // Another open preview saved this number first: read again and pick the next one.
  if (error.code === "23505" || /not the next version/.test(error.message ?? "")) return "duplicate";
  throw error;
}
