from datetime import UTC, datetime, timedelta

from app.security.passwords import hash_password, verify_password
from app.security.sessions import ArmazenamentoDeSessoes


def test_senha_e_armazenada_com_hash_e_verificada_sem_expor_valor() -> None:
    senha_hash = hash_password("Senha123")

    assert senha_hash != "Senha123"
    assert senha_hash.startswith("scrypt$")
    assert verify_password("Senha123", senha_hash)
    assert not verify_password("Outra123", senha_hash)


def test_sessao_expira_em_trinta_minutos() -> None:
    agora = [datetime(2026, 9, 8, 12, 0, tzinfo=UTC)]
    sessoes = ArmazenamentoDeSessoes(relogio=lambda: agora[0])

    identificador = sessoes.criar("1", "doador")
    assert sessoes.buscar(identificador) is not None
    assert sessoes.buscar(identificador).expira_em == agora[0] + timedelta(minutes=30)

    agora[0] += timedelta(minutes=30)
    assert sessoes.buscar(identificador) is None
