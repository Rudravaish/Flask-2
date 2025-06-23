# Vercel Deployment Guide

## Overview
This Flask application has been modified to work with Vercel's serverless environment. The main changes include:

1. **No file system writes** - Images are processed in memory
2. **Simplified ML model** - Uses mock predictions instead of heavy PyTorch models
3. **Lighter dependencies** - Removed heavy ML libraries for Vercel compatibility

## Files for Vercel Deployment

- `main_vercel.py` - Vercel-compatible Flask app
- `vercel.json` - Vercel configuration
- `requirements.txt` - Lightweight dependencies
- `templates/index.html` - Frontend template
- `static/` - Static assets

## Deployment Steps

1. **Install Vercel CLI**:
   ```bash
   npm i -g vercel
   ```

2. **Login to Vercel**:
   ```bash
   vercel login
   ```

3. **Deploy**:
   ```bash
   vercel
   ```

4. **Follow the prompts**:
   - Link to existing project or create new
   - Set project name
   - Choose settings

## Limitations

### Current Limitations:
- **Mock Predictions**: The current version uses simplified mock predictions instead of real ML models
- **No File Storage**: Images are processed in memory and not saved
- **Limited ML Capabilities**: Heavy PyTorch models are not included

### For Production ML:
To use real ML predictions, you have several options:

1. **External ML API**: Use services like:
   - Google Cloud ML
   - AWS SageMaker
   - Azure ML
   - Hugging Face Inference API

2. **Separate ML Service**: Deploy ML models on:
   - Google Cloud Run
   - AWS Lambda
   - Heroku
   - Railway

3. **Edge ML**: Use lighter models that fit Vercel's limits:
   - TensorFlow Lite
   - ONNX Runtime
   - Smaller PyTorch models

## Environment Variables

Set these in Vercel dashboard:
- `SESSION_SECRET` - Flask session secret

## Custom Domain

After deployment, you can add a custom domain in the Vercel dashboard.

## Monitoring

- Check Vercel dashboard for function logs
- Monitor function execution times
- Watch for cold start issues

## Troubleshooting

### Common Issues:
1. **Function timeout**: Increase `maxDuration` in vercel.json
2. **Memory limits**: Reduce dependency size
3. **Cold starts**: Consider using Vercel Pro for better performance

### Debugging:
- Check Vercel function logs
- Test locally with `vercel dev`
- Monitor function metrics in dashboard 