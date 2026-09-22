from __future__ import annotations

import logging

from usuarios.models import Usuario

from .permissions import pode_editar_usuario

logger = logging.getLogger(__name__)


def _definir_senha(usuario: Usuario, nova_senha: str) -> None:
    # validate_password já rodou no clean() de quem chama (AtualizarUsuarioForm e AlterarMinhaSenhaForm).
    usuario.set_password(nova_senha)
    usuario.save(update_fields=["password"])


def redefinir_senha(*, ator: Usuario, alvo: Usuario, nova_senha: str) -> None:
    """Redefinição por um superior hierárquico — usada por AtualizarUsuarioForm.aplicar()."""
    if not pode_editar_usuario(ator, alvo):
        raise PermissionError("Ator sem permissão para redefinir a senha deste usuário.")
    _definir_senha(alvo, nova_senha)
    logger.info("Senha redefinida: executor_id=%s alvo_id=%s", ator.pk, alvo.pk)


def alterar_minha_senha(*, usuario: Usuario, nova_senha: str) -> None:
    """Autoalteração pela tela "Minha conta"; senha atual já conferida por AlterarMinhaSenhaForm.clean_old_password()."""
    _definir_senha(usuario, nova_senha)
    logger.info("Senha redefinida: executor_id=%s alvo_id=%s", usuario.pk, usuario.pk)
