from wtforms import Form, StringField, RadioField, SelectField, TextAreaField, validators

class CreateTradeInForm(Form):
    computer_component = SelectField('Enter Computer Component:',[validators.DataRequired()],choices=[("",'Select'),('GPU','Graphics-Card'),('CPU','Central-Processing-Unit'),('RAM','RAM'),('PowerSupply','Power-Supply'),('SSD','Storage'),('MotherBoard','MotherBoard')],default="")
    part_types = StringField('Enter Type Of Component(GPU:3060ti, CPU:i5, RAM:8GB, STORGE:500GB, MB:MotherBoard or PS:PowerSupply):',[validators.length(min=1, max=12),validators.DataRequired()])
    condition = RadioField('Condition',choices=[('Broken','Broken'),('Well-Used','Well-Used'),('Barely-Used','Barely-Used'),('Perfect','Perfect')],default="")
    remarks = TextAreaField('Remarks',[validators.Optional()])
