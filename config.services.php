<?php

/**
 * Laravel Services Configuration for CV Analyzer
 * Add this to your config/services.php file
 */

return [
    // ... other service configurations

    'cv_analyzer' => [
        // The base URL of the CV Analyzer service
        'url' => env('CV_ANALYZER_API_URL', 'http://159.69.75.59:8001'),
        
        // Request timeout in seconds
        'timeout' => env('CV_ANALYZER_TIMEOUT', 30),
        
        // Number of retries on failure
        'retries' => env('CV_ANALYZER_RETRIES', 3),
        
        // API Key (if needed in future)
        'api_key' => env('CV_ANALYZER_API_KEY', null),
    ],
];
