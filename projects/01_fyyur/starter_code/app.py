#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import FlaskForm
from forms import *
from flask_migrate import Migrate
from datetime import datetime, timezone
from flask import request, render_template, flash
from flask_wtf.csrf import CSRFProtect

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# TODO: connect to a local postgresql database
# Done in config.py

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime



###routes
@app.route('/')
def index():
  return render_template('pages/home.html')
#  Venues
#  ----------------------------------------------------------------
@app.route('/venues')
def venues():
    
  # TODO: replace with real venues data.
  #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
  # Fetch distinct city-state combinations
    distinct_locations = db.session.query(Venue.city, Venue.state).distinct().all()
    
    # Prepare the final data structure
    data = []
    
    for location in distinct_locations:
        # Fetch all venues in the current city and state
        venues_in_location = Venue.query.filter_by(city=location.city, state=location.state).all()
        
        venue_list = []
        for venue in venues_in_location:
            # Count the number of upcoming shows for each venue
            num_upcoming_shows = Show.query.filter(
                Show.venue_id == venue.id, 
                Show.start_time > datetime.now()
            ).count()
            
            # Add venue details
            venue_list.append({
                "id": venue.id,
                "name": venue.name,
                "num_upcoming_shows": num_upcoming_shows
            })
        
        # Add city and state grouping
        data.append({
            "city": location.city,
            "state": location.state,
            "venues": venue_list
        })
    
    # Render the template with dynamic data
    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  search_term = request.form.get('search_term', '')
  search_results = Venue.search(search_term)
  response = {
        "count": len(search_results),
        "data": [
            {
                "id": venue.id,
                "name": venue.name,
                "num_upcoming_shows": Show.query.filter(
                    Show.venue_id == venue.id, 
                    Show.start_time > datetime.now()
                ).count()
            }
            for venue in search_results
        ]
    }
  return render_template('pages/search_venues.html', results=response, search_term=search_term)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id

  venue = Venue.query.get_or_404(venue_id)
  past_shows = []
  upcoming_shows = []
  for show in venue.shows:
        show_data = {
            "artist_id": show.artist.id,
            "artist_name": show.artist.name,
            "artist_image_link": show.artist.image_link,
            "start_time": show.start_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        }
        if show.start_time > datetime.now():
            upcoming_shows.append(show_data)
        else:
            past_shows.append(show_data)


  venue_data = {
        "id": venue.id,
        "name": venue.name,
        "genres": venue.genres.split(','),  
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website_link,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows),
    }

  return render_template('pages/show_venue.html', venue=venue_data)

class Venue(db.Model):
    __tablename__ = 'venues'
    id = db.Column(db.Integer, primary_key=True)    
    name = db.Column(db.String(),nullable=False)

    city = db.Column(db.String(120),nullable=False)
    state = db.Column(db.String(120),nullable=False)
    address = db.Column(db.String(120),nullable=False)
    phone = db.Column(db.String(120),nullable=False)
    
    genres = db.Column(db.ARRAY(db.String()),nullable=False)
    image_link = db.Column(db.String(500),nullable=False)
    facebook_link = db.Column(db.String(120),nullable=False)
    website_link = db.Column(db.String(120),nullable=False)

    seeking_talent=db.Column(db.Boolean,nullable=False,default = False)
    seeking_description =  db.Column(db.String(500),nullable=False)
    shows = db.relationship('Show', backref='venue', lazy='joined',cascade='all, delete')
    @classmethod
    def search(cls, search_term):
        return cls.query.filter(cls.name.ilike(f'%{search_term}%')).all()
    def __repr__(self):
      return f'<Venue {self.id} {self.name}>'

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

class Artist(db.Model):
    __tablename__ = 'artists'
    id = db.Column(db.Integer, primary_key=True)    
    name = db.Column(db.String,nullable=False)

    city = db.Column(db.String(120),nullable=False)
    state = db.Column(db.String(120),nullable=False)
    phone = db.Column(db.String(120),nullable=False)

    genres = db.Column(db.ARRAY(db.String()),nullable=False)
    image_link = db.Column(db.String(500),nullable=False)
    facebook_link = db.Column(db.String(120),nullable=False)
    website_link = db.Column(db.String(120),nullable=False)
    seeking_venue= db.Column(db.Boolean, default=False)
    seeking_description=db.Column(db.String(500),nullable=False)

    shows = db.relationship('Show', backref='artist', lazy='joined',cascade='all, delete')
    
    def __repr__(self):
      return f'<Artist {self.id} {self.name}>'


#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  form = VenueForm(request.form)
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  if form.validate():
    try:
        # Create a new Venue instance with form data
        new_venue = Venue(
            name=form.name.data,
            city=form.city.data,
            state=form.state.data,
            address=form.address.data,
            phone=form.phone.data,
            genres=form.genres.data,
            image_link=form.image_link.data,
            facebook_link=form.facebook_link.data,
            website_link=form.website_link.data,
            seeking_talent=form.seeking_talent.data,
            seeking_description=form.seeking_description.data
        )
        db.session.add(new_venue)
        db.session.commit()
        # on successful db insert, flash success
        flash(f'Venue {form.name.data} was successfully listed!', 'success')
        return redirect(url_for('index'))
    except Exception as e:
        # Rollback in case of error
        db.session.rollback()

        # Flash an error message
        flash(f'An error occurred. Venue {form.name.data} could not be listed.', 'error')
        return redirect(url_for('create_venue_form'))
        print(f"Error: {e}")  # Log the error for debugging
    finally:
        # Close the database session
        db.session.close()

    # Redirect to the home page
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  try:
        # Query the venue by ID
        venue_to_delete = Venue.query.get_or_404(venue_id)
        db.session.delete(venue)
        db.session.commit()
        flash(f'Venue {venue.name} was successfully deleted!', 'success')
        return redirect(url_for('index'))
  except Exception as e:
        # Rollback if an error occurs
        db.session.rollback()
        flash(f'An error occurred. Venue {venue.name} could not be deleted.', 'error')
        
  finally:
        # Close the database session
        db.session.close()
  # TODO: Complete this endpoint for taking a venue_id, and using
  return None  # or use `render_template('pages/home.html')`

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  try: #try, except structure (Logic Flow)
  # TODO: replace with real data returned from querying the database
    artists_query = Artist.query.all()
    data = [{
          "id": artist.id,
          "name": artist.name
      } for artist in artists_query]
    return render_template('pages/artists.html', artists=data)
  except Exception as e:
      print(f"Error fetching artists: {e}")

        # Flash an error message if needed
      flash("An error occurred while fetching the artists.", "error")
      return redirect(url_for('index'))
  
@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  search_term = request.form.get('search_term', '')
  try:
      artists_query = Artist.search(search_term)
      
      artists = Artist.search(search_term)
      response ={
          "count": len(artists_query),
            "data": [
                {
                    "id": artist.id,
                    "name": artist.name,
                    "num_upcoming_shows": len([show for show in artist.shows if show.start_time > datetime.now()])
                }
                for artist in artists_query
            ]
      }
      return render_template('pages/search_artists.html', results=response, search_term=search_term)
  except Exception as e:
      print(f"An error occurred: {e}")
      flash("An error occurred while searching for artists.", "error")
      return redirect(url_for('artists'))
      
@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id
  artist = Artist.query.get(artist_id)


  if not artist:
        # If the artist is not found, return a 404 error or a custom page
      return render_template('errors/404.html')
  
  past_shows = []
  upcoming_shows = []
  current_time = datetime.now(timezone.utc)
  #check Artisit and add to past_shows
  for show in artist.shows:
        artists_shows_data ={
                "venue_id": show.venue.id,
                "venue_name": show.venue.name,
                "venue_image_link": show.venue.image_link,
                "start_time": show.start_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            }
        
        if show.start_time < current_time:
            past_shows.append(artists_shows_data)
        else:
            upcoming_shows.append(artists_shows_data)
            
          


  data = {
        "id": artist.id,
        "name": artist.name,
        "genres": artist.genres,
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link,
        
    }
  data['past_shows']= past_shows
  data['upcoming_shows']= upcoming_shows
  data['past_shows_count']= len(past_shows)
  data['upcoming_shows_count']= len(upcoming_shows)
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  artist = Artist.query.get(artist_id)
  if artist is None:
        flash('Artist not found.', 'error')
        return redirect(url_for('artists'))
  
  form = ArtistForm(obj=artist)

  artist = {
        "id": artist_id,
        "name": artist.name,
        "genres": artist.genres,
        "city": artist.city,
        "state": artist.state,
        # Put the dashes back into phone number
        "phone": (artist.phone[:3] + '-' + artist.phone[3:6] + '-' + artist.phone[6:]),
        "website_link": artist.website_link,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link
    }

  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  try:
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
    artist = Artist.query.get(artist_id)
    if artist is None:
          return render_template('errors/404.html')
    form = ArtistForm(obj=artist)
    artist.name = request.form.get('name')
    artist.city = request.form.get('city')
    artist.state = request.form.get('state')
    artist.phone = request.form.get('phone')
    artist.genres = request.form.getlist('genres')  # Assuming genres is a multi-select field
    artist.facebook_link = request.form.get('facebook_link')
    artist.website = request.form.get('website')
    artist.seeking_venue = True if request.form.get('seeking_venue') == 'y' else False
    artist.seeking_description = request.form.get('seeking_description')
    artist.image_link = request.form.get('image_link')

        # Commit changes to the database
    db.session.commit()
    flash(f'Artist {artist.name} was successfully updated!')
  except Exception as e:
    db.session.rollback()
    flash(f'An error occurred. Artist could not be updated. Error: {str(e)}')
  finally:
        # Close the session
    db.session.close()

    # Redirect to the updated artist's detail page
  return redirect(url_for('show_artist', artist_id=artist_id))
       

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):

  #fetch value from the database
  venue = Venue.query.get(venue_id)
  
  #check if the venue is found
  if venue is None:
      return render_template('errors/404.html')
  form = VenueForm(obj=venue)
  venue={
    "id": venue_id,
    "name": venue.name,
    "genres": venue.genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website_link": venue.website_link,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link
  }
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  # Fetch the existing venue from the database
  try:
      
      venue = Venue.query.get(venue_id)
    
    # If the venue is not found, show an error
      if venue is None:
        flash('Venue not found.', 'error')
        return redirect(url_for('venues'))
      form = VenueForm(obj=venue)
      if form.validate_on_submit():
        venue.name = form.name.data
        venue.city = form.city.data
        venue.state = form.state.data
        venue.address = form.address.data
        venue.phone = form.phone.data
        venue.genres = form.genres.data  # genres should be a list of selected genres
        venue.facebook_link = form.facebook_link.data
        venue.website_link = form.website_link.data
        venue.seeking_talent = form.seeking_talent.data
        venue.seeking_description = form.seeking_description.data
        venue.image_link = form.image_link.data
        db.session.commit()
        flash(f'Venue {venue.name} was successfully updated!')
      else:
          flash('There were errors with your form submission.', 'error')


      # Flash a success message
      
  
  except Exception as e:
      db.session.rollback()
      flash('An error occurred. Venue could not be updated.', 'error')
    
  finally:
        # Close the database session
        db.session.close()

    # Redirect to the updated venue's detail page
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
    form = ArtistForm(request.form)

    if form.validate():
        try:
            new_artist = Artist(
              name=form.name.data,
              city=form.city.data,
              state=form.state.data,
              phone=form.phone.data,
              facebook_link=form.facebook_link.data,
              website=form.website_link.data,
              image_link=form.image_link.data,
              seeking_venue=form.seeking_venue.data,
              seeking_description=form.seeking_description.data)
            db.session.add(new_artist)
            db.session.commit()
            flash('Artist ' + request.form['name'] + ' was successfully listed!')
        except Exception as e:
            
            db.session.rollback()
            flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
        finally:
           db.session.close()
    else:
        flash('Form validation failed. Please check your inputs.')
            
    return render_template('pages/home.html')

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.=
  shows_query = Show.query.join(Artist).join(Venue).all()
  data = []
  for show in shows_query:
        data.append({
            "venue_id": show.venue_id,
            "venue_name": show.venue.name,
            "artist_id": show.artist_id,
            "artist_name": show.artist.name,
            "artist_image_link": show.artist.image_link,
            "start_time": show.start_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ')  # Convert to ISO 8601 format
        })
  return render_template('pages/shows.html', shows=data)
  

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  try:
      venue_id = request.form['venue_id']
      artist_id = request.form['artist_id']
      start_time = request.form['start_time']
      new_show = Show(venue_id=venue_id, artist_id=artist_id, start_time=start_time)
      db.session.add(new_show)
      db.session.commit()
      flash('Show was successfully listed!')
  except Exception as e:
      db.session.rollback()
      flash(f'An error occurred. Show could not be listed. Error: {str(e)}')
  finally:
      db.session.close()

  return render_template('pages/home.html')
  
  

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
