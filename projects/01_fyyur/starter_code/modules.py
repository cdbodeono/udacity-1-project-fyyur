from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


    

    
class Show(db.Model):
   __tablename__='shows'   
   id= db.Column(db.Integer,primary_key=True)  
   venue_id= db.Column(db.Integer,db.ForeignKey('venues.id'),nullable=False)  
   artist_id= db.Column(db.Integer,db.ForeignKey('artists.id'),nullable=False)    
   start_time = db.Column(db.DateTime,nullable=True) 
   artists = db.relationship('Artist', backref='show_artist', lazy='joined',cascade='all, delete')
   venues = db.relationship('Venue', backref='show_venue', lazy='joined',cascade='all, delete')
   
   def __repr__(self):
      return f'<Show {self.id} {self.venue_id} {self.start_time}>'
   