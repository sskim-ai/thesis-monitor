//! Exact task-local Sol binding; legacy guard paths are not aliases for this scope.
use super::{Checked, Policy, digest};
use serde::Deserialize;
use serde_json::Value;
use std::fs;
use std::os::unix::fs::{MetadataExt, PermissionsExt};
use std::path::{Component, Path, PathBuf};

pub(super) const PROFILE: &str = "SOL_61_HIGH_EXECUTION_V1";
const TASK: &str = "C21G_SOL_HIGH_GUARDED_HOST_COMPATIBILITY_AND_SINGLE_NO_SEND_CANARY";

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Scope {
    task: String,
    execution_profile: String,
    account: String,
    security: String,
    owner_sha256: String,
    source_generation: String,
    root: PathBuf,
    ledger: PathBuf,
    stage_seconds: u64,
    input_bytes: usize,
    output_bytes: usize,
    retries: u32,
}

fn scope_matches(s: &Scope, p: &Policy) -> Checked<()> {
    if s.task != TASK || p.task != s.task || s.execution_profile != PROFILE
        || p.execution_profile.as_deref() != Some(PROFILE)
        || s.account.is_empty() || p.account.as_deref() != Some(s.account.as_str())
        || p.security != s.security || p.owner_sha256 != s.owner_sha256
        || p.source_generation != s.source_generation || p.ledger != s.ledger
        || !s.root.is_absolute() || s.root.components().any(|c| c == Component::ParentDir)
        || s.ledger != s.root.join("inference-ledger.json")
        || s.stage_seconds != 600 || s.input_bytes != 393216 || s.output_bytes != 131072 || s.retries != 0
        || !["BLIND", "ADJ"].contains(&p.stage.as_str())
        || [&p.owner_sha256, &p.prompt_sha256, &p.request_sha256].iter()
            .any(|s| s.len() != 64 || !s.bytes().all(|c| c.is_ascii_hexdigit()))
    { return Err("SOL_SCOPE_BINDING"); }
    Ok(())
}

fn plain_ancestors(path: &Path) -> Checked<()> {
    for parent in path.ancestors() {
        if fs::symlink_metadata(parent).map_err(|_| "SOL_PATH_STAT")?.file_type().is_symlink() {
            return Err("SOL_PATH_SYMLINK");
        }
    }
    Ok(())
}

pub(super) fn validate_policy(p: &Policy) -> Checked<bool> {
    let file = std::env::var_os("TM_SOL_TASK_SCOPE");
    if p.execution_profile.is_none() && p.account.is_none() && file.is_none() { return Ok(false); }
    if p.execution_profile.as_deref() != Some(PROFILE) { return Err("SOL_PROFILE"); }
    let file = PathBuf::from(file.ok_or("SOL_SCOPE_MISSING")?);
    plain_ancestors(&file)?;
    let meta = fs::symlink_metadata(&file).map_err(|_| "SOL_SCOPE_STAT")?;
    if !meta.is_file() || meta.nlink() != 1 || meta.len() > 8192
        || meta.permissions().mode() & 0o222 != 0 { return Err("SOL_SCOPE_IDENTITY"); }
    let bytes = fs::read(&file).map_err(|_| "SOL_SCOPE_READ")?;
    let expected = std::env::var("TM_SOL_TASK_SCOPE_SHA256").map_err(|_| "SOL_SCOPE_PIN_MISSING")?;
    if digest(&bytes) != expected { return Err("SOL_SCOPE_DIGEST"); }
    let scope: Scope = serde_json::from_slice(&bytes).map_err(|_| "SOL_SCOPE_FORMAT")?;
    scope_matches(&scope, p)?;
    plain_ancestors(&scope.root)?;
    if scope.root.canonicalize().map_err(|_| "SOL_ROOT")? != scope.root { return Err("SOL_ROOT_CANONICAL"); }
    Ok(true)
}

pub(super) fn validate_records(rows: &[Value], p: &Policy) -> Checked<()> {
    if p.execution_profile.as_deref() != Some(PROFILE) { return Ok(()); }
    if rows.iter().any(|r| r["execution_profile"] != PROFILE
        || r["account"].as_str() != p.account.as_deref()
        || r["owner_sha256"] != p.owner_sha256 || r["source_generation"] != p.source_generation
        || r["model"] != "gpt-6.1-sol" || r["effort"] != "high") {
        return Err("SOL_LEDGER_BINDING");
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;
    fn pair() -> (Scope, Policy) {
        let s = Scope { task:TASK.into(), execution_profile:PROFILE.into(), account:"ACCOUNT".into(),
            security:"SYNTHETIC_SECURITY".into(), owner_sha256:"a".repeat(64), source_generation:"DATED_SOURCE".into(),
            root:"/private/tmp/synthetic-sol-scope".into(), ledger:"/private/tmp/synthetic-sol-scope/inference-ledger.json".into(),
            stage_seconds:600,input_bytes:393216,output_bytes:131072,retries:0 };
        let p = Policy { task:s.task.clone(),execution_profile:Some(PROFILE.into()),account:Some(s.account.clone()),
            stage:"BLIND".into(),security:s.security.clone(),owner_sha256:s.owner_sha256.clone(),prompt_sha256:"b".repeat(64),
            request_sha256:"c".repeat(64),thread_id:"fresh-blind".into(),source_generation:s.source_generation.clone(),
            schema:json!({}),schema_binding:None,started_unix:1,deadline_unix:601,ledger:s.ledger.clone() };
        (s,p)
    }
    #[test] fn exact_scope_blind_and_adj() { let(s,mut p)=pair();assert!(scope_matches(&s,&p).is_ok());p.stage="ADJ".into();p.thread_id="fresh-adj".into();assert!(scope_matches(&s,&p).is_ok()); }
    #[test] fn old_task_is_not_a_sol_alias() { let(s,mut p)=pair();p.task="POSCO_P1_FLEXIBLE_OUTPUT_20261101".into();assert!(scope_matches(&s,&p).is_err()); }
    #[test] fn old_or_changed_ledger_denied() { let(s,mut p)=pair();p.ledger="/private/tmp/old/inference-ledger.json".into();assert!(scope_matches(&s,&p).is_err()); }
    #[test] fn account_subject_source_and_packet_bound() { for field in 0..4 {let(s,mut p)=pair();match field {0=>p.account=Some("OTHER".into()),1=>p.security="OTHER".into(),2=>p.source_generation="OTHER".into(),_=>p.owner_sha256="d".repeat(64)};assert!(scope_matches(&s,&p).is_err());} }
    #[test] fn exact_profile_required() { let(s,mut p)=pair();p.execution_profile=Some("ASTRA_XHIGH_EXECUTION_V1".into());assert!(scope_matches(&s,&p).is_err()); }
    #[test] fn path_and_limit_changes_denied() {for field in 0..6 {let(mut s,p)=pair();match field {0=>s.root="relative".into(),1=>s.ledger="/private/tmp/wrong.json".into(),2=>s.retries=1,3=>s.stage_seconds=601,4=>s.input_bytes=393217,_=>s.output_bytes=131073};assert!(scope_matches(&s,&p).is_err());} }
    #[test] fn sol_model_and_effort_exact() {
        let schema=json!({"type":"object"});let catalog=json!([{"type":"function","name":"synthetic"}]);
        for (model,effort,allowed) in [("gpt-6.1-sol","high",true),("gpt-6-astra","xhigh",false),("gpt-6.1-sol","medium",false),("other","high",false)] {
            let b=json!({"model":model,"reasoning":{"effort":effort},"stream":true,"tools":catalog,"text":{"format":{"schema":schema}}});
            assert_eq!(super::super::inspect_profile(&serde_json::to_vec(&b).unwrap(),&schema,&catalog,"gpt-6.1-sol","high").is_ok(),allowed);
        }
    }
    #[test] fn ledger_cannot_inherit_another_profile() { let(_,p)=pair();assert!(validate_records(&[],&p).is_ok());assert!(validate_records(&[json!({"execution_profile":"ASTRA_XHIGH_EXECUTION_V1"})],&p).is_err()); }
    #[test] fn changed_prompt_request_and_schema_not_accepted_by_legacy_guards() {
        let(_,mut p)=pair();p.prompt_sha256="not-a-hash".into();let(s,_)=pair();assert!(scope_matches(&s,&p).is_err());
        p.prompt_sha256="b".repeat(64);p.request_sha256="not-a-hash".into();assert!(scope_matches(&s,&p).is_err());
        assert!(super::super::validate_schema_binding(&json!({}),None).is_err());
    }
}
