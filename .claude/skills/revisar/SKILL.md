---
description: Revisão final antes de considerar a tarefa concluída no ambiente Django/Python. Verificar padrões (PEP8), produção, segurança, uso do ORM e tratamento de erros.
invoke: manual
---

Revise todo o código alterado nesta sessão garantindo:

**Padrões (Python & Django)**
- Código segue as convenções PEP8 (nomenclatura, espaçamento).
- Respeita a estrutura do Django (Fat Models / Thin Views ou services isolados, uso correto de forms/serializers).
- Uso eficiente do ORM: Sem consultas "N+1" (verifica necessidade de `select_related` ou `prefetch_related`).
- Sem consultas SQL cruas (`raw()`) a não ser que estritamente necessário e justificado.

**Produção**
- Sem `print()`, `breakpoint()`, `pdb`, `TODO` ou código de debug esquecido.
- Uso correto do módulo `logging` para registros.
- Variáveis de ambiente usadas via `os.environ`, `decouple` ou similar (nada hardcoded).
- Configurações críticas (como `DEBUG`, `SECRET_KEY`, `ALLOWED_HOSTS`) não estão vazando no código analisado.

**Segurança**
- Proteções nativas do Django mantidas (CSRF ativo em formulários/POST, XSS evitado não abusando do filtro `|safe` nos templates).
- Controle de acesso verificado nas Views/Endpoints (uso de `@login_required`, `LoginRequiredMixin`, `permission_classes` do DRF).
- Inputs de usuários são validados via Django Forms ou DRF Serializers (nunca confiando no `request.POST` ou `request.data` diretamente).
- Uploads de arquivo com validação estrita de tipo e tamanho.

**LGPD**
- Minimização: Dados pessoais coletados e serializados são apenas os mínimos necessários (cuidado com `fields = '__all__'` em serializers/forms contendo dados pessoais).
- Dados sensíveis têm tratamento reforçado.
- Logs (`logging`) não gravam dados pessoais em texto claro (senhas, CPFs, e-mails).
- Retenção/Exclusão: Se aplicável à task, o direito ao esquecimento e a deleção em cascata (`on_delete`) foram modelados corretamente e de forma segura.

**Robustez**
- Integridade de dados: Mutações complexas no banco de dados estão protegidas por `with transaction.atomic():`.
- Casos extremos cobertos (`None`, QuerySets vazias, valores inesperados).
- Sem condições de corrida óbvias (ex: uso de `select_for_update()` se houver concorrência financeira/estoque).

**Tratamento de erros**
- Erros capturados via `try/except` em blocos específicos (evitando `except Exception:` genérico sempre que possível).
- Uso de atalhos seguros como `get_object_or_404` para evitar retornos `500` quando deveria ser `404`.
- Mensagens de erro informativas para o usuário, garantindo que stack traces e erros internos da aplicação nunca sejam expostos no front-end.

Ao final, liste de forma objetiva o que foi corrigido por você nesta revisão e o que ficou pendente para minha intervenção manual.