# setup_vendor.ps1 - Simplified version without Node.js

# Create static directories
New-Item -ItemType Directory -Path static/css -Force
New-Item -ItemType Directory -Path static/fonts -Force

# Download Font Awesome
$fontAwesomeVersion = "6.4.0"
Invoke-WebRequest "https://use.fontawesome.com/releases/v$fontAwesomeVersion/fontawesome-free-$fontAwesomeVersion-web.zip" -OutFile fontawesome.zip
Expand-Archive fontawesome.zip -DestinationPath static/fontawesome
Move-Item static/fontawesome/fontawesome-free-$fontAwesomeVersion-web/css/all.min.css static/css/fontawesome.css
Move-Item static/fontawesome/fontawesome-free-$fontAwesomeVersion-web/webfonts static/fonts/fontawesome
Remove-Item fontawesome.zip -Force
Remove-Item static/fontawesome -Recurse -Force

# Create vendor script include
Set-Content templates/includes/vendor_scripts.html @"
<!-- Pre-built Tailwind CSS from CDN -->
<link href="https://cdn.jsdelivr.net/npm/tailwindcss@3.3.5/dist/tailwind.min.css" rel="stylesheet">

<!-- Custom CSS for theme variables -->
<style>
:root {
  --color-primary: 59, 130, 246;
  --color-secondary: 107, 114, 128;
  --color-success: 34, 197, 94;
  --color-danger: 239, 68, 68;
  --color-dark-800: 31, 41, 55;
  --color-dark-900: 17, 24, 39;
}

.dark {
  --color-primary: 37, 99, 235;
  --color-secondary: 75, 85, 99;
  --color-success: 22, 163, 74;
  --color-danger: 220, 38, 38;
}

/* Add your custom styles here */
</style>

<!-- Font Awesome -->
<link href="{{ url_for('static', filename='css/fontawesome.css') }}" rel="stylesheet">
"@

Write-Host "Vendor setup completed successfully - no build process needed!"