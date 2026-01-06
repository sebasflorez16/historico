"""
Formularios para la aplicación de informes
"""

from django import forms
from decimal import Decimal
from .models import Informe


class RegistrarPagoForm(forms.Form):
    """
    Formulario para registrar pagos de informes
    """
    monto = forms.DecimalField(
        label='Monto a Pagar (COP)',
        max_digits=10,
        decimal_places=2,
        min_value=Decimal('0.01'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 50000.00',
            'step': '0.01'
        })
    )
    
    metodo_pago = forms.ChoiceField(
        label='Método de Pago',
        choices=[
            ('', '-- Seleccione --'),
            ('efectivo', 'Efectivo'),
            ('transferencia', 'Transferencia Bancaria'),
            ('tarjeta_credito', 'Tarjeta de Crédito'),
            ('tarjeta_debito', 'Tarjeta de Débito'),
            ('pse', 'PSE'),
            ('otro', 'Otro'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    referencia_pago = forms.CharField(
        label='Referencia de Pago',
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Número de transacción, comprobante, etc.'
        })
    )
    
    notas = forms.CharField(
        label='Notas / Observaciones',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Información adicional sobre el pago...'
        })
    )
    
    def __init__(self, *args, informe=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.informe = informe
        
        # Si hay informe, validar que el monto no exceda el saldo
        if informe:
            self.fields['monto'].help_text = f'Saldo pendiente: ${informe.saldo_pendiente:,.2f} COP'
    
    def clean_monto(self):
        monto = self.cleaned_data.get('monto')
        
        if self.informe:
            if monto > self.informe.saldo_pendiente:
                raise forms.ValidationError(
                    f'El monto no puede exceder el saldo pendiente de ${self.informe.saldo_pendiente:,.2f} COP'
                )
        
        return monto


class AplicarDescuentoForm(forms.Form):
    """
    Formulario para aplicar descuentos a informes
    """
    porcentaje = forms.DecimalField(
        label='Porcentaje de Descuento (%)',
        max_digits=5,
        decimal_places=2,
        min_value=Decimal('0.01'),
        max_value=Decimal('100.00'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 15.00',
            'step': '0.01',
            'min': '0.01',
            'max': '100'
        })
    )
    
    notas = forms.CharField(
        label='Motivo del Descuento',
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Razón del descuento: cliente frecuente, promoción, etc.'
        })
    )
    
    def __init__(self, *args, informe=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.informe = informe
        
        if informe:
            self.fields['porcentaje'].help_text = f'Precio base: ${informe.precio_base:,.2f} COP'


class EditarPrecioForm(forms.ModelForm):
    """
    Formulario para editar precio base de un informe
    """
    class Meta:
        model = Informe
        fields = ['precio_base', 'fecha_vencimiento']
        widgets = {
            'precio_base': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'Precio en COP'
            }),
            'fecha_vencimiento': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            })
        }
        labels = {
            'precio_base': 'Precio Base (COP)',
            'fecha_vencimiento': 'Fecha de Vencimiento'
        }
