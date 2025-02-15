from app import app, db, DeliveryCompany, DeliveryPrice

wilayas = [
    'أدرار', 'الشلف', 'الأغواط', 'أم البواقي', 'باتنة', 'بجاية', 'بسكرة', 'بشار', 'البليدة', 'البويرة',
    'تمنراست', 'تبسة', 'تلمسان', 'تيارت', 'تيزي وزو', 'الجزائر', 'الجلفة', 'جيجل', 'سطيف', 'سعيدة',
    'سكيكدة', 'سيدي بلعباس', 'عنابة', 'قالمة', 'قسنطينة', 'المدية', 'مستغانم', 'المسيلة', 'معسكر', 'ورقلة',
    'وهران', 'البيض', 'إليزي', 'برج بوعريريج', 'بومرداس', 'الطارف', 'تندوف', 'تيسمسيلت', 'الوادي', 'خنشلة',
    'سوق أهراس', 'تيبازة', 'ميلة', 'عين الدفلى', 'النعامة', 'عين تموشنت', 'غرداية', 'غليزان',
    'المغير', 'المنيعة', 'أولاد جلال', 'برج باجي مختار', 'بني عباس', 'تيميمون', 'تقرت', 'جانت',
    'عين صالح', 'عين قزام', 'تسابيت'
]

with app.app_context():
    # Get ZR Express company
    company = DeliveryCompany.query.filter_by(name='zr_express').first()
    if company:
        # Delete existing prices for ZR Express
        DeliveryPrice.query.filter_by(delivery_company_id=company.id).delete()
        
        # Add default prices for all wilayas
        # Using 500 DA for home delivery and 400 DA for office delivery as example prices
        for wilaya in wilayas:
            price = DeliveryPrice(
                delivery_company_id=company.id,
                wilaya=wilaya,
                home_delivery_price=500,  # Default home delivery price
                office_delivery_price=400  # Default office delivery price
            )
            db.session.add(price)
        
        try:
            db.session.commit()
            print("Successfully added prices for all wilayas for ZR Express")
        except Exception as e:
            db.session.rollback()
            print(f"Error adding prices: {str(e)}")
    else:
        print("Error: ZR Express company not found")
