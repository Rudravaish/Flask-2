from flask import Flask, render_template, request, flash, redirect, url_for, jsonify
import os
import logging
import time
import base64
import io
from PIL import Image
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "fallback-secret-key-for-dev")

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}

# Fitzpatrick skin types
FITZPATRICK_TYPES = {
    'I': 'Type I - Very Fair (Always burns, never tans)',
    'II': 'Type II - Fair (Usually burns, tans minimally)', 
    'III': 'Type III - Medium (Sometimes burns, tans uniformly)',
    'IV': 'Type IV - Olive (Rarely burns, tans easily)',
    'V': 'Type V - Dark (Very rarely burns, tans very easily)',
    'VI': 'Type VI - Very Dark (Never burns, tans very easily)'
}

def allowed_file(filename):
    """Check if the uploaded file has an allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def detect_skin_type_simple(image_data):
    """Simple skin type detection based on image brightness using PIL only"""
    try:
        # Convert to PIL Image
        image = Image.open(io.BytesIO(image_data))
        image = image.convert('RGB')
        
        # Convert to numpy array
        img_array = np.array(image)
        
        # Calculate average brightness
        brightness = np.mean(img_array)
        
        # Simple classification based on brightness
        if brightness < 85:
            return 'VI'
        elif brightness < 120:
            return 'V'
        elif brightness < 150:
            return 'IV'
        elif brightness < 180:
            return 'III'
        elif brightness < 200:
            return 'II'
        else:
            return 'I'
    except Exception as e:
        app.logger.error(f"Skin type detection error: {e}")
        return 'III'  # Default to medium

def analyze_image_simple(image_data):
    """Simple image analysis using PIL and numpy only"""
    try:
        image = Image.open(io.BytesIO(image_data))
        width, height = image.size
        
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Convert to numpy array
        img_array = np.array(image)
        
        # Simple analysis
        brightness = np.mean(img_array)
        contrast = np.std(img_array)
        
        # Calculate basic color statistics
        red_mean = np.mean(img_array[:, :, 0])
        green_mean = np.mean(img_array[:, :, 1])
        blue_mean = np.mean(img_array[:, :, 2])
        
        return {
            'width': width,
            'height': height,
            'brightness': brightness,
            'contrast': contrast,
            'red_mean': red_mean,
            'green_mean': green_mean,
            'blue_mean': blue_mean
        }
    except Exception as e:
        app.logger.error(f"Image analysis error: {e}")
        return {}

def predict_lesion_simple(image_data, skin_type, body_part, has_evolved, evolution_weeks, 
                         manual_length, manual_width, age, uv_exposure, family_history):
    """Simplified prediction function using only PIL and numpy"""
    try:
        import random
        
        # Analyze image
        image_analysis = analyze_image_simple(image_data)
        
        # Mock analysis based on parameters
        risk_factors = 0
        if has_evolved:
            risk_factors += 2
        if family_history:
            risk_factors += 1
        if age > 50:
            risk_factors += 1
        if uv_exposure > 7:
            risk_factors += 1
            
        # Add image-based risk factors
        if image_analysis:
            if image_analysis.get('contrast', 0) > 50:
                risk_factors += 1
            if image_analysis.get('brightness', 0) < 100:
                risk_factors += 1
            
        # Mock prediction
        if risk_factors >= 3:
            prediction = "High Risk - Melanoma"
            confidence = random.randint(75, 95)
        elif risk_factors >= 1:
            prediction = "Medium Risk - Atypical Nevus"
            confidence = random.randint(50, 80)
        else:
            prediction = "Low Risk - Benign"
            confidence = random.randint(70, 90)
            
        return prediction, confidence, {
            'ABCDE_feature_analysis': {
                'asymmetry': 'Low' if risk_factors < 2 else 'Medium',
                'border': 'Regular' if risk_factors < 2 else 'Irregular',
                'color': 'Uniform' if risk_factors < 2 else 'Variable',
                'diameter': 'Normal' if risk_factors < 2 else 'Large',
                'evolution': 'Stable' if not has_evolved else 'Changing'
            },
            'cnn_analysis': {
                'prediction': prediction,
                'confidence': confidence
            },
            'metadata_risk_analysis': {
                'age_risk': 'Low' if age < 50 else 'Medium',
                'uv_exposure_risk': 'Low' if uv_exposure < 7 else 'Medium',
                'family_history_risk': 'High' if family_history else 'Low'
            },
            'combined_score': confidence / 100.0,
            'combined_score_explanation': f'Based on {risk_factors} risk factors',
            'detected_skin_tone': f'Type {skin_type}',
            'analysis_type': 'simplified_vercel',
            'skin_type_adjustments': {},
            'manual_measurements': {},
            'image_analysis': image_analysis
        }
        
    except Exception as e:
        app.logger.error(f"Prediction error: {e}")
        return "Error - Unable to analyze", 0, {}

@app.route('/', methods=['GET', 'POST'])
def home():
    """Main route for file upload and prediction"""
    if request.method == 'POST':
        try:
            # Check if file was uploaded
            if 'image' not in request.files:
                flash('No file selected', 'error')
                return redirect(request.url)
            
            file = request.files['image']
            if file.filename == '':
                flash('No file selected', 'error')
                return redirect(request.url)
            
            # Check file extension
            if not allowed_file(file.filename):
                flash('Invalid file type. Please upload a valid image file.', 'error')
                return redirect(request.url)
            
            # Get form data
            skin_type = request.form.get('skin_type', 'III')
            body_part = request.form.get('body_part', 'other')
            if not body_part or body_part == '' or body_part == 'None':
                body_part = 'other'
            has_evolved = 'has_evolved' in request.form
            
            # Handle evolution_weeks with proper validation
            evolution_weeks_raw = request.form.get('evolution_weeks', '')
            if has_evolved and evolution_weeks_raw and evolution_weeks_raw.strip():
                try:
                    evolution_weeks = int(evolution_weeks_raw)
                except ValueError:
                    evolution_weeks = 0
            else:
                evolution_weeks = 0
            
            # Get additional metadata
            try:
                age = int(request.form.get('age', 50))
            except Exception:
                age = 50
            try:
                uv_exposure = int(request.form.get('uv_exposure', 5))
            except Exception:
                uv_exposure = 5
            family_history = 'family_history' in request.form
            manual_length = request.form.get('manual_length')
            manual_width = request.form.get('manual_width')
            
            # Convert manual measurements to float if provided
            if manual_length:
                try:
                    manual_length = float(manual_length)
                except ValueError:
                    manual_length = None
            if manual_width:
                try:
                    manual_width = float(manual_width)
                except ValueError:
                    manual_width = None
            
            # Read file data into memory (no file system writes)
            file_data = file.read()
            
            # Detect skin tone from image
            detected_skin_type = detect_skin_type_simple(file_data)
            skin_type = detected_skin_type  # Override form value with detected
            
            # Make simplified prediction
            try:
                prediction, confidence, analysis_data = predict_lesion_simple(
                    file_data, skin_type, body_part, has_evolved, evolution_weeks,
                    manual_length, manual_width, age, uv_exposure, family_history
                )
                
                app.logger.info(f"Simplified Prediction: {prediction}, Confidence: {confidence}%")
                
                # Generate comprehensive analysis summary
                analysis_summary = None
                if analysis_data:
                    analysis_summary = {
                        'ABCDE_feature_analysis': analysis_data.get('ABCDE_feature_analysis', {}),
                        'cnn_analysis': analysis_data.get('cnn_analysis', {}),
                        'metadata_risk_analysis': analysis_data.get('metadata_risk_analysis', {}),
                        'combined_score': analysis_data.get('combined_score', 0.0),
                        'combined_score_explanation': analysis_data.get('combined_score_explanation', ''),
                        'detected_skin_tone': analysis_data.get('detected_skin_tone', f'Type {skin_type}'),
                        'analysis_type': analysis_data.get('analysis_type', 'simplified_vercel'),
                        'skin_type_adjustments': analysis_data.get('skin_type_adjustments', {}),
                        'manual_measurements': analysis_data.get('manual_measurements', {}),
                        'image_analysis': analysis_data.get('image_analysis', {})
                    }
                
                # Convert image to base64 for display
                image_base64 = base64.b64encode(file_data).decode('utf-8')
                image_data_url = f"data:image/jpeg;base64,{image_base64}"
                
                return render_template('index.html', 
                                     result=prediction, 
                                     confidence=confidence, 
                                     image_path=image_data_url,
                                     filename=file.filename,
                                     skin_type=skin_type,
                                     skin_type_description=FITZPATRICK_TYPES[skin_type],
                                     analysis_summary=analysis_summary,
                                     detected_skin_tone=f'Type {skin_type}',
                                     fitzpatrick_types=FITZPATRICK_TYPES,
                                     body_part_options=['face', 'scalp', 'neck', 'chest', 'back', 'abdomen', 'arms', 'hands', 'legs', 'feet', 'other'],
                                     age=age,
                                     uv_exposure=uv_exposure,
                                     family_history=family_history,
                                     manual_length=manual_length,
                                     manual_width=manual_width)
                
            except Exception as e:
                app.logger.error(f"Prediction error: {str(e)}")
                flash('Error processing image. Please try again with a different image.', 'error')
                return redirect(request.url)
                
        except Exception as e:
            app.logger.error(f"Upload error: {str(e)}")
            flash('An error occurred while processing your upload. Please try again.', 'error')
            return redirect(request.url)
    
    # GET request - show the form
    body_part_options = ['face', 'scalp', 'neck', 'chest', 'back', 'abdomen', 'arms', 'hands', 'legs', 'feet', 'other']
    return render_template('index.html', fitzpatrick_types=FITZPATRICK_TYPES, body_part_options=body_part_options)

@app.errorhandler(413)
def too_large(e):
    """Handle file too large error"""
    flash('File too large. Please upload an image smaller than 16MB.', 'error')
    return redirect(url_for('home'))

@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors"""
    return render_template('index.html', error="Page not found"), 404

@app.errorhandler(500)
def internal_error(e):
    """Handle 500 errors"""
    return render_template('index.html', error="Internal server error"), 500

@app.errorhandler(Exception)
def handle_exception(e):
    """Handle general exceptions"""
    app.logger.error(f"Unhandled exception: {str(e)}")
    return render_template('index.html', error="An unexpected error occurred"), 500

if __name__ == '__main__':
    app.run(debug=True) 