from flask_admin.contrib.sqla import ModelView
from models import *
from wtforms import SelectMultipleField, SelectField
from wtforms.widgets import ListWidget, CheckboxInput
from wtforms.validators import ValidationError

class MultiCheckboxField(SelectMultipleField):
    widget = ListWidget(prefix_label=False)
    option_widget = CheckboxInput()

class StudenteView(ModelView):
    column_list = ["matricola", "nome", "cognome", "mail", "permessi"]
    form_columns = ["matricola", "nome", "cognome", "mail", "permessi"]
    column_searchable_list = ["matricola", "nome", "cognome"]
    form_extra_fields = {
        "permessi": MultiCheckboxField("Permessi", choices=[
            ("RIC", "Ricevimento"),
            ("ESM", "Esame"),
            ("TIR", "Tirocinio")
        ] 
        )
    }

    def search_placeholder(self):
        return "Inserire nome, cognome o matricola studente"

    def on_model_change(self, form, model, is_created):
        permessi = form.permessi.data
        if not permessi:
            raise ValidationError("Devi selezionare almeno un permesso.")
        model.set_permessi = set(permessi)

class EventoView(ModelView):
    can_edit = False
    column_list = ["tipo", "tipoSlot", "inizio", "fine", "frequenza", "count", "until"]
    form_columns = ["tipo", "tipoSlot", "inizio", "fine" ,"frequenza", "count", "until"]
    column_formatters = {
        "inizio": lambda v, c, m, p: m.inizio.strftime("%d/%m/%Y - %H:%M"),
        "fine": lambda v, c, m, p: m.fine.strftime("%d/%m/%Y - %H:%M"),
        "until": lambda v, c, m, p: m.until.strftime("%d/%m/%Y - %H:%M") if m.until else ""
    }

    form_overrides = {
        "tipo": SelectField,
        "tipoSlot": SelectField,
        "frequenza": SelectField
    }

    form_args = {
        "tipo": {
            "choices": [(choice.name, choice.value) for choice in TipoEvento]
        },
        "tipoSlot": {
            "choices": [(choice.name, choice.value) for choice in TipoSlot]
        },
        "frequenza": {
            "choices": [(choice.name, choice.value) for choice in Frequenze]
        }
    }
    column_searchable_list = ["inizio"]

    def search_placeholder(self):
        return "Ricerca per data (mm-dd-yyyy)"

    def on_model_change(self, form, model, is_created):
        if form.fine.data <= form.inizio.data:
            raise ValidationError("La data di fine evento deve essere successiva a quella di inizio")
        if not form.until.data and not form.count.data:
            raise ValidationError("Specificare almeno un termine per la ricorrenza")
        if form.until.data and form.count.data:
            raise ValidationError("Specificare solo un termine per la ricorrenza")
        if form.until.data:
            if form.until.data <= form.fine.data:
                raise ValidationError("Data termine ricorrenza non valida")
            else:
                model.count = None
        elif form.count.data:
            if form.count.data <= 0:
                raise ValidationError("Numero di ricorrenze deve essere maggiore di 0")
            else:
                model.until = None

    
class RicorrenzaView(ModelView):
    can_create = False
    can_edit = False
    column_list = ["tipo", "tipoSlot", "inizio", "fine"] 
    column_formatters = {
        "inizio": lambda v, c, m, p: m.inizio.strftime("%d/%m/%Y - %H:%M"),
        "fine": lambda v, c, m, p: m.fine.strftime("%d/%m/%Y - %H:%M"),
    }
    column_searchable_list = ["inizio"]

    def search_placeholder(self):
        return "Ricerca per data (mm-dd-yyyy)"

    def on_model_change(self, form, model, is_created):
        if form.fine.data <= form.inizio.data:
            raise ValidationError("La data di fine deve essere successiva a quella di inizio")

class SlotView(ModelView):
    can_create = False
    column_list = ["tipo", "inizio", "fine", "stato", "note", "studente"]
    column_formatters = {
        "inizio": lambda v, c, m, p: m.inizio.strftime("%d/%m/%Y - %H:%M"),
        "fine": lambda v, c, m, p: m.fine.strftime("%d/%m/%Y - %H:%M"),
    }
    column_editable_list = ["note"]
    column_searchable_list = ["inizio", "studente.nome", "studente.cognome", "studente.matricola"]

    def search_placeholder(self):
        return "Ricerca per data o studente"

def create_admin(admin, db):
    admin.add_view(StudenteView(Studente, db.session))
    admin.add_view(EventoView(Evento, db.session))
    admin.add_view(RicorrenzaView(Ricorrenza, db.session))
    admin.add_view(SlotView(Slot, db.session))
