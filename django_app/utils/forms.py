"""Mixins de formulaires partagés — accessibilité (feature 015)."""


class AccessibleFormMixin:
    """Ajoute aria-describedby="error_<champ>" à chaque champ du formulaire.

    Lie chaque champ à l'emplacement où son message d'erreur est rendu dans
    le template (id="error_<champ>" role="alert"), sans dupliquer cette
    règle dans chaque classe de formulaire. Si aucune erreur n'est rendue,
    l'attribut pointe vers un id inexistant — ignoré silencieusement par
    les technologies d'assistance (comportement standard de aria-describedby).
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs.setdefault("aria-describedby", f"error_{name}")
