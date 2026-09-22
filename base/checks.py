from django.conf import settings
from django.core.checks import Warning, register

# (chave de settings, chave do default, id do check, o que fica incompleto)
_CAMPOS_INSTITUCIONAIS = (
    (
        "NOME_INSTITUICAO",
        "NOME_INSTITUICAO_DEFAULT",
        "base.W001",
        "os Termos de Uso e a Política de Privacidade publicados ficam com "
        "texto de placeholder",
    ),
    (
        "EMAIL_CONTATO_DPO",
        "EMAIL_CONTATO_DPO_DEFAULT",
        "base.W002",
        "o contato de exercício de direitos LGPD nos Termos de Uso e na "
        "Política de Privacidade fica com um e-mail que não existe",
    ),
    (
        "FORO_COMARCA",
        "FORO_COMARCA_DEFAULT",
        "base.W003",
        "a cláusula de foro dos Termos de Uso fica incompleta",
    ),
)


@register()
def checar_dados_institucionais(app_configs, **kwargs):
    """
    Com DEBUG=False, avisa se NOME_INSTITUICAO/EMAIL_CONTATO_DPO/FORO_COMARCA
    ainda estão nos defaults de core/settings.py — sem isso, os Termos de Uso
    e a Política de Privacidade publicados ficam com texto de placeholder
    (inclusive um contato de DPO que não existe), sem que nada avise.
    É Warning, não Error: ao contrário da SECRET_KEY (que quebra o start por
    ser insegura sem valor), a instituição pode legitimamente ainda não ter
    decidido esses dados — isto só precisa aparecer no `manage.py check` do
    deploy.
    """
    if settings.DEBUG:
        return []

    problemas = []
    for chave, chave_default, id_check, consequencia in _CAMPOS_INSTITUCIONAIS:
        if getattr(settings, chave) == getattr(settings, chave_default):
            problemas.append(
                Warning(
                    f"{chave} não foi definido no .env — {consequencia}.",
                    id=id_check,
                )
            )
    return problemas
