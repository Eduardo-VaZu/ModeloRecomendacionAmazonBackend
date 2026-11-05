"""Caso de uso: reemplazar los datos del prototipo por un paquete demo nuevo."""

from __future__ import annotations

from pathlib import Path

from ..shared.base_handler import BaseHandler
from .demo_bundle_reader import DemoBundleReader
from .import_demo_bundle_request import ImportDemoBundleRequest
from .import_demo_bundle_response import ImportDemoBundleResponse


class ImportDemoBundleHandler(BaseHandler[ImportDemoBundleRequest, ImportDemoBundleResponse]):
    """Vacía las tablas e importa el paquete en una sola transacción."""

    async def execute(self, request: ImportDemoBundleRequest) -> ImportDemoBundleResponse:
        reader = DemoBundleReader(Path(request.directory))
        unit = self._unit_of_work
        repositories = (
            unit.dataset_summaries,
            unit.products,
            unit.demo_users,
            unit.interactions,
            unit.recommendations,
            unit.experiment_results,
            unit.hypothesis_tests,
            unit.vi_indicators,
        )
        for repository in repositories:
            await repository.delete_all()

        summary = reader.summary()
        products = reader.products()
        users = reader.users()
        interactions = reader.interactions()
        recommendations = reader.recommendations()
        results = reader.experiment_results()
        tests = reader.hypothesis_tests()
        indicators = reader.vi_indicators()

        await unit.dataset_summaries.create(summary)
        await unit.products.bulk_create(products)
        await unit.demo_users.bulk_create(users)
        await unit.interactions.bulk_create(interactions)
        await unit.recommendations.bulk_create(recommendations)
        await unit.experiment_results.bulk_create(results)
        await unit.hypothesis_tests.bulk_create(tests)
        await unit.vi_indicators.bulk_create(indicators)
        await unit.commit()

        return ImportDemoBundleResponse(
            is_synthetic=summary.is_synthetic,
            products=len(products),
            users=len(users),
            interactions=len(interactions),
            recommendations=len(recommendations),
            experiment_results=len(results),
            hypothesis_tests=len(tests),
            vi_indicators=len(indicators),
        )
