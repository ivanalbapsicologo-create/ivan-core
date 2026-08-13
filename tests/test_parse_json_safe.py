"""parse_json_safe: la garantía de tolerancia en la que confían los consumidores."""

from ivan_core.llm.base import parse_json_safe


def test_json_directo():
    assert parse_json_safe('{"a": 1}') == {"a": 1}


def test_code_fence():
    assert parse_json_safe('```json\n{"a": 1}\n```') == {"a": 1}


def test_json_reparable():
    # Coma colgante: json.loads falla, json_repair lo rescata.
    assert parse_json_safe('{"a": 1,}') == {"a": 1}


def test_basura_devuelve_valor_falsy():
    # Conducta real: json_repair convierte texto arbitrario en '' (string vacía),
    # que escapa al contrato declarado dict|list pero es falsy — los consumidores
    # (`_coerce_to_list`, checks de required keys) la tratan como fallo. Este test
    # fija la garantía mínima: NUNCA texto no-vacío sin parsear.
    result = parse_json_safe("no hay json aquí")
    assert not result


def test_lista_valida():
    assert parse_json_safe('[1, 2, 3]') == [1, 2, 3]
