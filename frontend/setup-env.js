const fs = require('fs');
const path = require('path');

// Path to the root .env file
const rootEnvPath = path.join(__dirname, '..', '.env');
// Path to the frontend .env file
const frontendEnvPath = path.join(__dirname, '.env');

// Copy the file
try {
  if (fs.existsSync(rootEnvPath)) {
    fs.copyFileSync(rootEnvPath, frontendEnvPath);
    console.log('Successfully copied .env file to frontend directory');
  } else {
    console.error('Root .env file not found');
  }
} catch (error) {
  console.error('Error copying .env file:', error);
}