"""
Cadeias de classe Tailwind compartilhadas entre templates e widgets de form.

Fica fora de templatetags/ para que forms.py possa importar sem depender da
camada de template. Só a identidade visual mora aqui — espaçamento e largura
continuam no ponto de uso.
"""
from __future__ import annotations

CLASSE_CAMPO = (
    "w-full border border-gray-300 px-3 py-2 text-sm rounded-sm "
    "focus:outline-none focus:border-tjgo-blue focus:ring-1 focus:ring-tjgo-blue"
)

CLASSES_BOTAO = {
    "primario": (
        "bg-tjgo-blue hover:bg-tjgo-light-blue text-white font-bold "
        "rounded shadow-sm transition"
    ),
    "secundario": (
        "bg-tjgo-gray-card hover:bg-gray-300 text-tjgo-navy font-bold "
        "rounded shadow-sm transition"
    ),
    "perigo": (
        "bg-red-600 hover:bg-red-700 text-white font-bold "
        "rounded shadow-sm transition"
    ),
}
