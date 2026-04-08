# CV Analyzer Service

Professional CV analysis service built with FastAPI and Python for skill extraction and candidate filtering.

## Features

- **PDF Parsing**: Extract text from PDF CVs
- **Skill Extraction**: Automatically detect technical skills using pattern matching and NLP
- **Categorization**: Organize skills by category (languages, frameworks, databases, DevOps, etc.)
- **Skill Matching**: Match extracted skills against a comprehensive skills database
- **Desired Skills**: Filter candidates based on desired technologies (FastAPI, Python, Laravel, etc.)
- **Match Scoring**: Calculate candidate match score based on skill relevance
- **Batch Processing**: Analyze multiple CVs at once
- **RESTful API**: Easy integration with Laravel and other applications

## Supported Skills

### Languages
Python, PHP, Java, JavaScript, TypeScript, C#, C++, Go, Rust, Ruby, Swift, Kotlin, Scala

### Frameworks
- **Python**: FastAPI, Django, Flask, Celery
- **PHP**: Laravel, Symfony, CodeIgniter, Yii
- **JavaScript/Node.js**: React, Vue, Angular, Next.js, Express, Nest.js

### Databases
MySQL, PostgreSQL, MongoDB, Redis, Elasticsearch, SQLite, Oracle, SQL Server, Cassandra, DynamoDB

### DevOps & Cloud
Docker, Kubernetes, Jenkins, CI/CD, AWS, Azure, GCP, Terraform, Ansible, Git

### Testing
pytest, unittest, PHPUnit, Jest, Selenium, Cypress, Mocha

## Installation

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### Setup

1. **Navigate to the service directory**:
```bash
cd cv-analyzer-service
```

2. **Create virtual environment**:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

4. **Copy environment file**:
```bash
cp .env.example .env
```

5. **Start the service**:
```bash
# Windows
run.bat

# Linux/Mac
bash run.sh

# Or directly with uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The service will be available at `http://localhost:8000`

## API Endpoints

### Health Check
```
GET /health
```
Check if the service is running.

**Response**:
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

### Analyze Single CV
```
POST /analyze-cv
```
Upload and analyze a single PDF CV.

**Parameters**:
- `file` (multipart/form-data): PDF file to analyze
- `min_score` (query, optional): Minimum match score filter (0-100)

**Response**:
```json
{
  "status": "success",
  "extracted_text": "John Doe...",
  "skills_found": [
    {
      "skill": "python",
      "confidence": 0.95,
      "category": "language"
    },
    {
      "skill": "fastapi",
      "confidence": 0.90,
      "category": "framework"
    }
  ],
  "technical_skills": ["python", "fastapi", "docker"],
  "framework_skills": ["fastapi", "django"],
  "language_skills": ["python"],
  "total_skills_count": 8,
  "has_desired_skills": true,
  "match_score": 85.5
}
```

### Batch Analyze CVs
```
POST /batch-analyze
```
Upload and analyze multiple PDF CVs at once.

**Parameters**:
- `files` (multipart/form-data): Multiple PDF files

**Response**:
```json
{
  "results": [
    {
      "filename": "john_doe.pdf",
      "status": "success",
      "technical_skills": ["python", "fastapi"],
      "match_score": 85.5,
      ...
    },
    {
      "filename": "jane_smith.pdf",
      "status": "success",
      "technical_skills": ["laravel", "mysql"],
      "match_score": 70.0,
      ...
    }
  ]
}
```

### Get Desired Skills
```
GET /desired-skills
```
Get the list of skills the system considers "desired".

**Response**:
```json
{
  "status": "success",
  "desired_skills": [
    "fastapi",
    "python",
    "laravel",
    "php",
    "react",
    "docker",
    ...
  ]
}
```

## Integration with Laravel

### 1. Create Service Class

Create `app/Services/Recruitment/CVAnalysisService.php`:

```php
<?php

namespace App\Services\Recruitment;

use Illuminate\Support\Facades\Http;
use Exception;

class CVAnalysisService
{
    private string $serviceUrl;

    public function __construct()
    {
        $this->serviceUrl = config('services.cv_analyzer.url', 'http://localhost:8000');
    }

    /**
     * Analyze a CV file
     */
    public function analyzeCv(string $filePath): array
    {
        try {
            $response = Http::timeout(60)
                ->attach('file', fopen($filePath, 'r'), basename($filePath))
                ->post("{$this->serviceUrl}/analyze-cv");

            if ($response->failed()) {
                throw new Exception("CV Analysis failed: {$response->body()}");
            }

            return $response->json();
        } catch (Exception $e) {
            return [
                'status' => 'error',
                'message' => $e->getMessage()
            ];
        }
    }

    /**
     * Filter candidates by minimum score
     */
    public function filterCandidatesByScore(array $candidates, float $minScore = 50.0): array
    {
        return array_filter($candidates, fn($c) => ($c['match_score'] ?? 0) >= $minScore);
    }
}
```

### 2. Add Configuration

Update `config/services.php`:

```php
'cv_analyzer' => [
    'url' => env('CV_ANALYZER_URL', 'http://localhost:8000'),
],
```

Add to `.env`:

```env
CV_ANALYZER_URL=http://localhost:8000
```

### 3. Use in Controller

```php
use App\Services\Recruitment\CVAnalysisService;

public function store(CandidateRequest $request): JsonResponse
{
    $analyzer = new CVAnalysisService();
    
    if ($request->hasFile('cv')) {
        $cvPath = $request->file('cv')->store('cvs');
        $analysis = $analyzer->analyzeCv(storage_path("app/{$cvPath}"));
        
        $request->merge([
            'skills' => implode(',', $analysis['technical_skills'] ?? []),
            'match_score' => $analysis['match_score'] ?? 0,
        ]);
    }
    
    // ... rest of store logic
}
```

## Customizing Desired Skills

Edit `app/utils/skills_database.py` to modify desired skills:

```python
DESIRED_SKILLS = [
    "fastapi",
    "python",
    "laravel",
    "php",
    # Add more as needed
]
```

## Skill Scoring System

Each skill has:
- **Category**: Type of skill (language, framework, database, etc.)
- **Priority**: Importance score (1-10)
- **Confidence**: How confident the extraction is (0-1)

The **Match Score** (0-100) is calculated based on:
- Number of languages found (up to 30 points)
- Number of frameworks (up to 40 points)
- Total technical skills (up to 30 points)
- Bonus for desired skills (up to 20 points)

## Error Handling

The service handles:
- Invalid PDF files
- File size limits (10MB max)
- Extraction failures
- Missing content

## Docker Deployment (Optional)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    python -m spacy download en_core_web_sm

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t cv-analyzer .
docker run -p 8000:8000 cv-analyzer
```

## Performance Tips

1. **Caching**: Cache analysis results for the same CV files
2. **Batch Processing**: Use `/batch-analyze` for multiple files
3. **Resource Allocation**: Allocate sufficient memory for PDF processing
4. **Database Indexing**: Index skill fields in Laravel for faster filtering

## Troubleshooting

### Port Already in Use
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -i :8000
kill -9 <PID>
```

### Import Errors
```bash
pip install --upgrade pdfplumber spacy
```

### PDF Extraction Issues
- Ensure PDF is not corrupted
- Check PDF file permissions
- Try with a different PDF

## Support

For issues or feature requests, check the logs in `storage/logs/` or run with debug:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-level debug
```

## License

MIT License
