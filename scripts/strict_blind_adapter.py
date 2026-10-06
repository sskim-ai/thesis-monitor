"""Native request adapter for the opt-in strict controller. No autonomous I/O."""
from copy import deepcopy

from app.services.unified_snapshot_contract import digest
from scripts import strict_blind_contract as contract
from scripts import strict_blind_comparison as comparison
from scripts.strict_blind_controller import RequestScope


def schema_authority():
    return dict(contract=contract.CONTRACT, builder="strict_blind_contract.response_schema",
        capabilities=deepcopy(contract.CAPABILITY_CONTRACT),
        axes=deepcopy(contract.AXES), subject_binding="exact source-only subset digest")


def authorities(plan, source_dag):
    """These are real locked contracts; invented fixtures are only transport data."""
    return dict(blind_rubric=deepcopy(contract.RUBRIC),
        blind_prompt=contract.PROMPT,
        blind_schema=schema_authority(),
        comparison=deepcopy(comparison.AUTHORITY), acceptance=deepcopy(comparison.ACCEPTANCE),
        blind_controller_policy=dict(model=plan["model"], effort=plan["effort"], timeout_seconds=600,
            retries=2, physical_cap=30, semantic_retry=False, mode="CLEAN_START"),
        monitoring_controller_policy=dict(model=plan["model"], effort=plan["effort"], timeout_seconds=600,
            retries=2, b2_physical_cap=30, semantic_retry=False, mode="CLEAN_START"),
        execution_plan=deepcopy(plan), source_dag=deepcopy(source_dag))


class BlindSubjectAdapter:
    def __init__(self, ticker):
        contract.require(bool(ticker), "BLIND_EMPTY_SUBJECTS")
        self.ticker = ticker

    def build(self, view):
        contract.require(set(view) == {"blind_package", "blind_rubric", "blind_prompt", "blind_schema"},
            "BLIND_UNDECLARED_VIEW")
        contract.require(view["blind_rubric"] == contract.RUBRIC and view["blind_prompt"] == contract.PROMPT,
            "BLIND_PROMPT_RUBRIC_DRIFT")
        contract.require(view["blind_schema"] == schema_authority(),
            "BLIND_CAPABILITY_SCHEMA_DRIFT")
        package = view["blind_package"]
        contract.require(package["rubric_sha256"] == digest(contract.RUBRIC), "BLIND_PACKAGE_RUBRIC_DRIFT")
        subject = package["subjects"][self.ticker]
        contract.require(subject["generation"] == package["generation"] and subject["ticker"] == self.ticker,
            "BLIND_SUBSET_IDENTITY")
        return contract.payload(subject)[0]


def register(controller):
    for slot in controller.contract["plan"]["stages"]["BLIND"]:
        contract.require(slot["scope"] == RequestScope.SUBJECT and len(slot["subjects"]) == 1,
            "BLIND_ONE_SUBJECT_PER_REQUEST")
        adapter = BlindSubjectAdapter(slot["subjects"][0])
        controller.register_adapter("blind_" + str(slot["batch"]), __file__, function_name=adapter.build.__qualname__)


def build_requests(controller):
    requests = []
    for index, slot in enumerate(controller.contract["plan"]["stages"]["BLIND"]):
        adapter = BlindSubjectAdapter(slot["subjects"][0])
        request = controller.project_request("BLIND", index, parents=["blind_package", "blind_rubric",
            "blind_prompt", "blind_schema"], adapter="blind_" + str(slot["batch"]), builder=adapter.build)
        subject = request["payload"]["input"]
        contract.require(subject["ticker"] == slot["subjects"][0] and subject["market"] == slot["market"],
            "BLIND_REQUEST_SLOT_BINDING")
        requests.append(request)
    return requests


class BlindValidation:
    """Backend-only source audit is never serialized into the provider payload."""
    def __init__(self, request, source_inputs):
        self.payload = deepcopy(request["payload"])
        self.subject, self.audit = contract.project_subject(source_inputs, generation=request["generation"])
        contract.require(self.payload == contract.payload(self.subject)[0], "BLIND_REQUEST_REPROJECTION_DRIFT")
        self.receipt = None

    def provider(self, output):
        return not contract.validate_json_schema(output, self.payload["response_schema"])

    def semantic(self, output):
        self.receipt = contract.validate_output(output, self.subject, self.audit)
        return self.receipt["status"] == "PASS"
