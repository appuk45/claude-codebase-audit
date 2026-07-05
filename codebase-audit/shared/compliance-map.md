# Compliance Map

Generated from the detection specs' inline `compliance_refs` (source of truth — do not hand-edit). Regenerate: `python -m engine.compliance`.

| checklist_id | controls |
|---|---|
| api_backward_compat | ISO25010 Compatibility |
| api_contract_docs | ISO25010 Interoperability |
| api_deprecation | ISO25010 Compatibility (Replaceability) |
| api_error_format | ISO25010 Interoperability; RFC 9457 |
| api_http_methods | ISO25010 Interoperability |
| api_idempotency | ISO25010 Interoperability; RFC 7231 |
| api_naming_consistency | ISO25010 Interoperability |
| api_pagination_consistency | ISO25010 Interoperability |
| api_status_codes | ISO25010 Interoperability |
| api_versioning | ISO25010 Compatibility (Replaceability) |
| arch_circular_deps | ISO25010 Modularity/Reliability |
| arch_cohesion | ISO25010 Modularity, Reusability |
| arch_coupling | ISO25010 Modularity |
| arch_dependency_direction | ISO25010 Modularity, Modifiability |
| arch_layering | ISO25010 Modularity |
| arch_module_boundaries | ISO25010 Modularity, Reusability |
| arch_pattern_consistency | ISO25010 Analysability, Modifiability |
| arch_scalability_bottleneck | ISO25010 Reliability, Performance Efficiency (Capacity) |
| arch_separation_concerns | ISO25010 Modularity, Analysability |
| dep_git_secrets | OWASP A03:2025 / A04:2025, CWE-798 |
| dep_install_scripts | OWASP A03:2025, CWE-506 |
| dep_known_cves | OWASP A03:2025, CWE-1395, CWE-937 |
| dep_license_compliance | OWASP A03:2025 (license integrity), SCVS |
| dep_lockfile | OWASP A03:2025, SCVS |
| dep_outdated_unmaintained | OWASP A03:2025 |
| dep_pinning | OWASP A03:2025, SCVS |
| dep_sbom | OWASP SCVS, A03:2025 |
| dep_source_integrity | OWASP A03:2025 |
| dep_typosquat | OWASP A03:2025, CWE-1357 |
| ent_backing_services | 12-Factor IV (Backing Services), ISO25010 Reliability |
| ent_build_release_run | 12-Factor V (Build/Release/Run), ISO25010 Reliability |
| ent_config_env | 12-Factor III (Config), ISO25010 Reliability |
| ent_config_validation | 12-Factor III, ISO25010 Reliability |
| ent_env_parity | 12-Factor X (Dev/Prod Parity), ISO25010 Reliability |
| ent_feature_flags | ISO25010 Reliability (Availability) |
| ent_graceful_shutdown | 12-Factor IX, ISO25010 Reliability |
| ent_health_checks | 12-Factor IX (Disposability), ISO25010 Reliability |
| ent_migrations | ISO25010 Reliability (Maturity) |
| ent_process_manager | 12-Factor VII/VIII, ISO25010 Reliability |
| ent_statelessness | 12-Factor VI (Stateless Processes), ISO25010 Reliability |
| i18n_charset_storage | ISO25010 Adaptability |
| i18n_encoding | ISO25010 Adaptability; W3C i18n |
| i18n_hardcoded_strings | ISO25010 Adaptability |
| i18n_locale_formatting | ISO25010 Adaptability |
| i18n_pluralization | ISO25010 Adaptability |
| i18n_rtl | ISO25010 Adaptability |
| i18n_string_concat | ISO25010 Adaptability |
| i18n_text_expansion | ISO25010 Adaptability |
| i18n_timezone | ISO25010 Adaptability |
| iac_base_image_pinning | CIS Docker 4.2 |
| iac_cloud_logging | CIS Cloud; OWASP A09:2025 (adjacent) |
| iac_container_nonroot | CIS Docker 4.1, CWE-250 |
| iac_encryption | CIS Cloud, CWE-311 |
| iac_iac_secrets | CIS Cloud, CWE-798 |
| iac_iam_least_privilege | CIS AWS IAM, CWE-269 |
| iac_image_hardening | CIS Docker 4.x |
| iac_image_secrets | CIS Docker 4.10, CWE-798 |
| iac_k8s_probes | CIS Kubernetes 5.x; ISO25010 Reliability |
| iac_k8s_resource_limits | CIS Kubernetes 5.x |
| iac_k8s_security_context | CIS Kubernetes 5.2, CWE-250 |
| iac_public_exposure | CIS AWS/Cloud, CWE-284 |
| issue_commented_code | ISO25010 Analysability |
| issue_complexity | ISO25010 Analysability/Modifiability/Testability |
| issue_dead_code | ISO25010 Analysability, Modifiability |
| issue_deep_nesting | ISO25010 Analysability |
| issue_duplication | ISO25010 Modifiability, Reusability |
| issue_error_swallowing | ISO25010 Modifiability; OWASP A10:2025 (adjacent) |
| issue_global_state | ISO25010 Modularity, Testability |
| issue_god_module | ISO25010 Modularity, Reusability |
| issue_long_unit | ISO25010 Analysability, Modularity |
| issue_mutable_default | ISO25010 Modifiability; CWE-1188 (adjacent) |
| issue_resource_leak | ISO25010 Reliability/Modifiability; CWE-772 |
| issue_todo_debt | ISO25010 Modifiability |
| issue_type_safety | ISO25010 Analysability, Modifiability |
| obs_audit_trail | OWASP A09:2025; ISO25010 Operability |
| obs_correlation_ids | ISO25010 Operability |
| obs_error_context | ISO25010 Operability; OWASP A09:2025 |
| obs_log_levels | ISO25010 Operability |
| obs_metrics | ISO25010 Operability |
| obs_monitoring_alerting | OWASP A09:2025; ISO25010 Operability |
| obs_pii_in_logs | OWASP A09:2025, CWE-532; GDPR/PCI-DSS |
| obs_security_event_logging | OWASP A09:2025, CWE-778 |
| obs_structured_logging | ISO25010 Operability |
| obs_tracing | ISO25010 Operability |
| perf_blocking_in_async | ISO25010 Time-Behaviour |
| perf_bounded_inputs | ISO25010 Capacity, OWASP API4:2023 (Unrestricted Resource Consumption) |
| perf_caching | ISO25010 Resource-Utilization |
| perf_connection_pool | ISO25010 Resource-Utilization |
| perf_fe_bundle | ISO25010 Resource-Utilization (proxy for LCP/INP) |
| perf_fe_images | ISO25010 Resource-Utilization (proxy for CLS) |
| perf_fe_render_blocking | ISO25010 Time-Behaviour (proxy for LCP) |
| perf_fe_virtualization | ISO25010 Time-Behaviour (proxy for INP) |
| perf_handler_compute | ISO25010 Time-Behaviour |
| perf_indexes | ISO25010 Time-Behaviour |
| perf_loop_io | ISO25010 Time-Behaviour |
| perf_n_plus_one | ISO25010 Time-Behaviour |
| perf_pagination | ISO25010 Resource-Utilization, Capacity |
| perf_response_compression | ISO25010 Resource-Utilization |
| perf_unbounded_memory | ISO25010 Resource-Utilization |
| res_bulkhead | ISO25010 Fault Tolerance |
| res_circuit_breaker | ISO25010 Fault Tolerance |
| res_dlq | ISO25010 Fault Tolerance, Recoverability |
| res_fallback | ISO25010 Fault Tolerance |
| res_fault_handling | ISO25010 Fault Tolerance |
| res_idempotent_consumer | ISO25010 Fault Tolerance |
| res_retries | ISO25010 Fault Tolerance |
| res_retry_safety | ISO25010 Fault Tolerance; RFC 7231 |
| res_timeouts | ISO25010 Fault Tolerance |
| sec_access_control | OWASP A01:2025, CWE-862 |
| sec_auth_hardening | OWASP A07:2025, CWE-307, CWE-347, CWE-521 |
| sec_authorization | OWASP A01:2025, CWE-639, CWE-285 |
| sec_cors | OWASP A01:2025, CWE-942 |
| sec_deserialization | OWASP A08:2025, CWE-502 |
| sec_error_leakage | OWASP A02:2025 / A10:2025, CWE-209 |
| sec_hardcoded_secrets | OWASP A04:2025, CWE-798 |
| sec_injection | OWASP A05:2025, CWE-89, CWE-78, CWE-94 |
| sec_misconfig | OWASP A02:2025, CWE-16, CWE-1188 |
| sec_path_traversal | OWASP A01:2025, CWE-22 |
| sec_security_headers | OWASP A02:2025, CWE-693 |
| sec_ssrf | OWASP A01:2025 (SSRF), CWE-918 |
| sec_tls_verification | OWASP A04:2025, CWE-295 |
| sec_weak_crypto | OWASP A04:2025, CWE-327, CWE-916 |
| sec_xss | OWASP A05:2025, CWE-79 |
