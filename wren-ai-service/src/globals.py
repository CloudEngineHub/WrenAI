import logging
from dataclasses import asdict, dataclass

import toml

from src.config import Settings
from src.core.pipeline import PipelineComponent
from src.core.provider import EmbedderProvider, LLMProvider
from src.pipelines import generation, indexing, retrieval
from src.utils import fetch_wren_ai_docs
from src.web.v1 import services

logger = logging.getLogger("wren-ai-service")


@dataclass
class ServiceContainer:
    ask_service: services.AskService
    question_recommendation: services.QuestionRecommendation
    relationship_recommendation: services.RelationshipRecommendation
    semantics_description: services.SemanticsDescription
    semantics_preparation_service: services.SemanticsPreparationService
    chart_service: services.ChartService
    chart_adjustment_service: services.ChartAdjustmentService
    sql_answer_service: services.SqlAnswerService
    sql_pairs_service: services.SqlPairsService
    sql_question_service: services.SqlQuestionService
    instructions_service: services.InstructionsService
    sql_correction_service: services.SqlCorrectionService


@dataclass
class ServiceMetadata:
    pipes_metadata: dict
    service_version: str


def create_service_container(
    pipe_components: dict[str, PipelineComponent],
    settings: Settings,
) -> ServiceContainer:
    query_cache = {
        "maxsize": settings.query_cache_maxsize,
        "ttl": settings.query_cache_ttl,
    }
    wren_ai_docs = fetch_wren_ai_docs(settings.doc_endpoint, settings.is_oss)
    if not wren_ai_docs:
        logger.warning("Failed to fetch Wren AI docs or response was empty.")

    return ServiceContainer(
        semantics_description=services.SemanticsDescription(
            pipelines={
                "semantics_description": generation.SemanticsDescription(
                    **pipe_components["semantics_description"],
                )
            },
            **query_cache,
        ),
        semantics_preparation_service=services.SemanticsPreparationService(
            pipelines={
                "db_schema": indexing.DBSchema(
                    **pipe_components["db_schema_indexing"],
                    column_batch_size=settings.column_indexing_batch_size,
                ),
                "historical_question": indexing.HistoricalQuestion(
                    **pipe_components["historical_question_indexing"],
                ),
                "table_description": indexing.TableDescription(
                    **pipe_components["table_description_indexing"],
                ),
                "sql_pairs": indexing.SqlPairs(
                    **pipe_components["sql_pairs_indexing"],
                    sql_pairs_path=settings.sql_pairs_path,
                ),
                "instructions": indexing.Instructions(
                    **pipe_components["instructions_indexing"],
                ),
                "project_meta": indexing.ProjectMeta(
                    **pipe_components["project_meta_indexing"],
                ),
            },
            **query_cache,
        ),
        ask_service=services.AskService(
            pipelines={
                "intent_classification": generation.IntentClassification(
                    **pipe_components["intent_classification"],
                    wren_ai_docs=wren_ai_docs,
                ),
                "misleading_assistance": generation.MisleadingAssistance(
                    **pipe_components["misleading_assistance"],
                ),
                "data_assistance": generation.DataAssistance(
                    **pipe_components["data_assistance"]
                ),
                "user_guide_assistance": generation.UserGuideAssistance(
                    **pipe_components["user_guide_assistance"],
                    wren_ai_docs=wren_ai_docs,
                ),
                "db_schema_retrieval": retrieval.DbSchemaRetrieval(
                    **pipe_components["db_schema_retrieval"],
                    table_retrieval_size=settings.table_retrieval_size,
                    table_column_retrieval_size=settings.table_column_retrieval_size,
                ),
                "historical_question": retrieval.HistoricalQuestionRetrieval(
                    **pipe_components["historical_question_retrieval"],
                    historical_question_retrieval_similarity_threshold=settings.historical_question_retrieval_similarity_threshold,
                ),
                "sql_pairs_retrieval": retrieval.SqlPairsRetrieval(
                    **pipe_components["sql_pairs_retrieval"],
                    sql_pairs_similarity_threshold=settings.sql_pairs_similarity_threshold,
                    sql_pairs_retrieval_max_size=settings.sql_pairs_retrieval_max_size,
                ),
                "instructions_retrieval": retrieval.Instructions(
                    **pipe_components["instructions_retrieval"],
                    similarity_threshold=settings.instructions_similarity_threshold,
                    top_k=settings.instructions_top_k,
                ),
                "sql_generation": generation.SQLGeneration(
                    **pipe_components["sql_generation"],
                    engine_timeout=settings.engine_timeout,
                ),
                "sql_generation_reasoning": generation.SQLGenerationReasoning(
                    **pipe_components["sql_generation_reasoning"],
                ),
                "followup_sql_generation_reasoning": generation.FollowUpSQLGenerationReasoning(
                    **pipe_components["followup_sql_generation_reasoning"],
                ),
                "sql_correction": generation.SQLCorrection(
                    **pipe_components["sql_correction"],
                    engine_timeout=settings.engine_timeout,
                ),
                "followup_sql_generation": generation.FollowUpSQLGeneration(
                    **pipe_components["followup_sql_generation"],
                    engine_timeout=settings.engine_timeout,
                ),
                "sql_regeneration": generation.SQLRegeneration(
                    **pipe_components["sql_regeneration"],
                    engine_timeout=settings.engine_timeout,
                ),
                "sql_functions_retrieval": retrieval.SqlFunctions(
                    **pipe_components["sql_functions_retrieval"],
                    engine_timeout=settings.engine_timeout,
                ),
            },
            allow_intent_classification=settings.allow_intent_classification,
            allow_sql_generation_reasoning=settings.allow_sql_generation_reasoning,
            allow_sql_functions_retrieval=settings.allow_sql_functions_retrieval,
            max_histories=settings.max_histories,
            enable_column_pruning=settings.enable_column_pruning,
            max_sql_correction_retries=settings.max_sql_correction_retries,
            **query_cache,
        ),
        chart_service=services.ChartService(
            pipelines={
                "sql_executor": retrieval.SQLExecutor(
                    **pipe_components["sql_executor"],
                    engine_timeout=settings.engine_timeout,
                ),
                "chart_generation": generation.ChartGeneration(
                    **pipe_components["chart_generation"],
                ),
            },
            **query_cache,
        ),
        chart_adjustment_service=services.ChartAdjustmentService(
            pipelines={
                "sql_executor": retrieval.SQLExecutor(
                    **pipe_components["sql_executor"],
                    engine_timeout=settings.engine_timeout,
                ),
                "chart_adjustment": generation.ChartAdjustment(
                    **pipe_components["chart_adjustment"],
                ),
            },
            **query_cache,
        ),
        sql_answer_service=services.SqlAnswerService(
            pipelines={
                "preprocess_sql_data": retrieval.PreprocessSqlData(
                    **pipe_components["preprocess_sql_data"],
                ),
                "sql_answer": generation.SQLAnswer(
                    **pipe_components["sql_answer"],
                    engine_timeout=settings.engine_timeout,
                ),
            },
            **query_cache,
        ),
        relationship_recommendation=services.RelationshipRecommendation(
            pipelines={
                "relationship_recommendation": generation.RelationshipRecommendation(
                    **pipe_components["relationship_recommendation"],
                    engine_timeout=settings.engine_timeout,
                )
            },
            **query_cache,
        ),
        question_recommendation=services.QuestionRecommendation(
            pipelines={
                "question_recommendation": generation.QuestionRecommendation(
                    **pipe_components["question_recommendation"],
                ),
                "db_schema_retrieval": retrieval.DbSchemaRetrieval(
                    **pipe_components["question_recommendation_db_schema_retrieval"],
                    table_retrieval_size=settings.table_retrieval_size,
                    table_column_retrieval_size=settings.table_column_retrieval_size,
                ),
                "sql_generation": generation.SQLGeneration(
                    **pipe_components["question_recommendation_sql_generation"],
                    engine_timeout=settings.engine_timeout,
                ),
                "sql_pairs_retrieval": retrieval.SqlPairsRetrieval(
                    **pipe_components["sql_pairs_retrieval"],
                    sql_pairs_similarity_threshold=settings.sql_pairs_similarity_threshold,
                    sql_pairs_retrieval_max_size=settings.sql_pairs_retrieval_max_size,
                ),
                "instructions_retrieval": retrieval.Instructions(
                    **pipe_components["instructions_retrieval"],
                    similarity_threshold=settings.instructions_similarity_threshold,
                    top_k=settings.instructions_top_k,
                ),
                "sql_functions_retrieval": retrieval.SqlFunctions(
                    **pipe_components["sql_functions_retrieval"],
                    engine_timeout=settings.engine_timeout,
                ),
            },
            allow_sql_functions_retrieval=settings.allow_sql_functions_retrieval,
            **query_cache,
        ),
        sql_pairs_service=services.SqlPairsService(
            pipelines={
                "sql_pairs": indexing.SqlPairs(
                    **pipe_components["sql_pairs_indexing"],
                    sql_pairs_path=settings.sql_pairs_path,
                )
            },
            **query_cache,
        ),
        sql_question_service=services.SqlQuestionService(
            pipelines={
                "sql_question_generation": generation.SQLQuestion(
                    **pipe_components["sql_question_generation"],
                )
            },
            **query_cache,
        ),
        instructions_service=services.InstructionsService(
            pipelines={
                "instructions_indexing": indexing.Instructions(
                    **pipe_components["instructions_indexing"],
                )
            },
            **query_cache,
        ),
        sql_correction_service=services.SqlCorrectionService(
            pipelines={
                "sql_tables_extraction": generation.SQLTablesExtraction(
                    **pipe_components["sql_tables_extraction"],
                ),
                "db_schema_retrieval": retrieval.DbSchemaRetrieval(
                    **pipe_components["db_schema_retrieval"],
                    table_retrieval_size=settings.table_retrieval_size,
                    table_column_retrieval_size=settings.table_column_retrieval_size,
                ),
                "sql_correction": generation.SQLCorrection(
                    **pipe_components["sql_correction"],
                    engine_timeout=settings.engine_timeout,
                ),
            },
            **query_cache,
        ),
    )


# Create a dependency that will be used to access the ServiceContainer
def get_service_container():
    from src.__main__ import app

    return app.state.service_container


def create_service_metadata(
    pipe_components: dict[str, PipelineComponent],
    pyproject_path: str = "pyproject.toml",
) -> ServiceMetadata:
    """
    This service metadata is used for logging purposes and will be sent to Langfuse.
    """

    def _get_version_from_pyproject() -> str:
        with open(pyproject_path, "r") as f:
            pyproject = toml.load(f)
            return pyproject["tool"]["poetry"]["version"]

    def _convert_pipe_metadata(
        llm_provider: LLMProvider,
        embedder_provider: EmbedderProvider,
        **_,
    ) -> dict:
        llm_metadata = (
            {
                "llm_model": llm_provider.get_model(),
                "llm_model_kwargs": llm_provider.get_model_kwargs(),
            }
            if llm_provider
            else {}
        )

        embedding_metadata = (
            {
                "embedding_model": embedder_provider.get_model(),
            }
            if embedder_provider
            else {}
        )
        return {**llm_metadata, **embedding_metadata}

    pipes_metadata = {
        pipe_name: _convert_pipe_metadata(**asdict(component))
        for pipe_name, component in pipe_components.items()
    }

    service_version = _get_version_from_pyproject()

    logger.info(f"Service version: {service_version}")

    return ServiceMetadata(pipes_metadata, service_version)


# Create a dependency that will be used to access the ServiceMetadata
def get_service_metadata():
    from src.__main__ import app

    return app.state.service_metadata
