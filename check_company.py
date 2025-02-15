from app import app, db, DeliveryCompany

with app.app_context():
    # Check if ZR Express exists
    company = DeliveryCompany.query.filter_by(name='zr_express').first()
    if not company:
        # Create ZR Express if it doesn't exist
        company = DeliveryCompany(name='zr_express')
        db.session.add(company)
        db.session.commit()
        print("Created ZR Express company")
    else:
        print("ZR Express company already exists")
