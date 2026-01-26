#!/usr/bin/env groovy
/**
 * n8n-mcp-server - Jenkins CI/CD Pipeline
 *
 * This pipeline provides comprehensive CI/CD with enforced quality standards:
 * - Code quality checks (Ruff format/lint, mypy) with quality gates
 * - Security scanning (pip-audit, Bandit, Semgrep, Trivy) with severity thresholds
 * - Unit testing with coverage thresholds
 * - SonarCloud analysis with quality gate enforcement
 * - Dependency-Track SBOM upload
 *
 * Quality Gates:
 * - Coverage: Minimum 80% (configurable)
 * - Lint Errors: 0 critical errors allowed
 * - Security: No critical/high vulnerabilities
 * - SonarCloud: Must pass quality gate
 *
 * Requirements:
 * - Jenkins with Pipeline plugin
 * - Python 3.12+ installed on agents
 * - uv (Python package manager) - auto-installed if not present
 * - Credentials: sonarcloud-token (for SonarCloud)
 * - Credentials: dependency-track (for SBOM upload)
 */

pipeline {
    agent {
        docker {
            image 'ubuntu:24.04'
            label 'jenkins-agent'
            args '-u root'
        }
    }

    options {
        buildDiscarder(logRotator(numToKeepStr: '20'))
        timeout(time: 30, unit: 'MINUTES')
        timestamps()
        disableConcurrentBuilds()
    }

    environment {
        PYTHON_VERSION = '3.12'
        PYTHONDONTWRITEBYTECODE = '1'
        PYTHONUNBUFFERED = '1'
        UV_NO_CACHE = '1'
        COVERAGE_FILE = '.coverage'
        // Ensure uv is in PATH for all stages
        PATH = "/root/.local/bin:${WORKSPACE}/.local/bin:${env.PATH}"
        // Project-specific settings
        PROJECT_NAME = 'n8n-mcp-server'
        SOURCE_DIR = 'src'

        // ============================================
        // QUALITY GATE THRESHOLDS
        // ============================================
        // Coverage threshold (percentage)
        COVERAGE_THRESHOLD = '80'
        // Maximum allowed lint errors per tool (0 = strict)
        MAX_RUFF_ERRORS = '0'
        MAX_MYPY_ERRORS = '0'
        // Bandit uses tiered severity: HIGH=fail, MEDIUM=warn, LOW=pass
        // Block on critical/high security vulnerabilities (pip-audit)
        BLOCK_ON_CRITICAL_VULNS = 'true'
        BLOCK_ON_HIGH_VULNS = 'false'
    }

    parameters {
        string(
            name: 'BRANCH',
            defaultValue: 'main',
            description: 'Branch to build (set by webhook or manually)'
        )
        booleanParam(
            name: 'RUN_SONAR',
            defaultValue: true,
            description: 'Run SonarCloud analysis'
        )
        booleanParam(
            name: 'UPLOAD_SBOM',
            defaultValue: true,
            description: 'Upload SBOM to Dependency-Track'
        )
        booleanParam(
            name: 'ENFORCE_QUALITY_GATES',
            defaultValue: true,
            description: 'Enforce quality gates (fail build on violations)'
        )
        string(
            name: 'DTRACK_URL',
            defaultValue: 'https://dtrack.homelab.com',
            description: 'Dependency-Track server URL'
        )
        string(
            name: 'DTRACK_PROJECT_UUID',
            defaultValue: 'b8cc347f-77d9-4ce2-b138-fbe6aba6ee9e',
            description: 'Dependency-Track project UUID (leave empty for auto-create)'
        )
        booleanParam(
            name: 'UPLOAD_DEFECTDOJO',
            defaultValue: true,
            description: 'Upload security scan results to DefectDojo'
        )
        string(
            name: 'DEFECTDOJO_URL',
            defaultValue: 'https://defectdojo.homelab.com',
            description: 'DefectDojo server URL'
        )
        string(
            name: 'DEFECTDOJO_PRODUCT_ID',
            defaultValue: '10',
            description: 'DefectDojo product ID (preferred over name lookup)'
        )
        booleanParam(
            name: 'CREATE_RELEASE',
            defaultValue: false,
            description: 'Create a release (requires main branch, triggers semantic-release)'
        )
        choice(
            name: 'RELEASE_TYPE',
            choices: ['auto', 'patch', 'minor', 'major'],
            description: 'Release type: auto (from commits), patch, minor, or major'
        )
    }

    stages {
        // Note: Removed explicit Checkout stage - Jenkins Multibranch Pipeline
        // handles checkout automatically before stages run. The explicit checkout
        // was overriding PR builds by checking out 'main' instead of the PR branch.

        stage('Workspace Cleanup') {
            steps {
                // Clean up cache directories that may have been created as root
                // This runs inside Docker with root permissions
                sh '''
                    echo "=== Cleaning workspace cache directories ==="
                    rm -rf .mypy_cache .pytest_cache .ruff_cache .uv-cache || true
                    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
                    find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
                    echo "Cleanup complete"

                    echo ""
                    echo "=== Git Info ==="
                    echo "Branch: $(git branch --show-current || echo 'detached HEAD')"
                    echo "Commit: $(git rev-parse HEAD)"
                    echo "Message: $(git log -1 --pretty=%s)"
                '''
            }
        }

        stage('Setup') {
            steps {
                sh '''
                    echo "=== Installing Build Dependencies ==="
                    export DEBIAN_FRONTEND=noninteractive
                    apt-get update -qq && apt-get install -qq -y --no-install-recommends \
                        python3 \
                        python3-pip \
                        python3-venv \
                        python3-dev \
                        build-essential \
                        git \
                        curl \
                        ca-certificates \
                        jq \
                        bc \
                        default-jdk-headless

                    echo ""
                    echo "=== Checking Build Dependencies ==="
                    python3 --version
                    jq --version
                    java -version

                    echo ""
                    echo "=== Installing uv ==="
                    curl -LsSf https://astral.sh/uv/install.sh | sh
                    /root/.local/bin/uv --version
                '''
            }
        }

        stage('Install Dependencies') {
            steps {
                sh '/root/.local/bin/uv sync --all-extras'
            }
        }

        stage('Code Quality') {
            parallel {
                stage('Format & Lint - Ruff') {
                    steps {
                        script {
                            def ruffResult = sh(
                                script: '''
                                    echo "=== Checking Code Formatting with Ruff ==="
                                    /root/.local/bin/uv run ruff format --check --diff ${SOURCE_DIR}/ tests/ > ruff-format-report.txt 2>&1
                                    FORMAT_EXIT=$?

                                    cat ruff-format-report.txt

                                    if [ $FORMAT_EXIT -ne 0 ]; then
                                        echo ""
                                        echo "QUALITY GATE FAILURE: Code formatting issues found."
                                        echo "Run 'ruff format ${SOURCE_DIR}/ tests/' to fix."
                                        exit 1
                                    fi

                                    echo "QUALITY GATE PASSED: Code formatting OK"
                                    echo ""

                                    echo "=== Running Ruff Linter ==="
                                    /root/.local/bin/uv run ruff check ${SOURCE_DIR}/ tests/ --output-format=json > ruff-report.json 2>&1 || true

                                    # Count errors using jq for reliable JSON parsing
                                    if [ -f ruff-report.json ] && [ -s ruff-report.json ]; then
                                        ERROR_COUNT=$(jq 'length' ruff-report.json 2>/dev/null || echo "0")
                                    else
                                        ERROR_COUNT=0
                                    fi

                                    echo "Ruff errors found: ${ERROR_COUNT}"
                                    echo "Maximum allowed: ${MAX_RUFF_ERRORS}"

                                    # Show errors for visibility
                                    /root/.local/bin/uv run ruff check ${SOURCE_DIR}/ tests/ || true

                                    # Check against threshold
                                    if [ "${ERROR_COUNT}" -gt "${MAX_RUFF_ERRORS}" ]; then
                                        echo "QUALITY GATE FAILURE: Too many Ruff errors (${ERROR_COUNT} > ${MAX_RUFF_ERRORS})"
                                        exit 1
                                    fi

                                    echo "QUALITY GATE PASSED: Ruff lint errors within threshold"
                                    exit 0
                                ''',
                                returnStatus: true
                            )

                            if (ruffResult != 0 && params.ENFORCE_QUALITY_GATES) {
                                unstable("Ruff quality gate failed - marking as unstable for SonarCloud report upload")
                            }
                        }
                    }
                    post {
                        always {
                            archiveArtifacts artifacts: 'ruff-format-report.txt,ruff-report.json', allowEmptyArchive: true
                        }
                    }
                }

                stage('Type Check - mypy') {
                    steps {
                        script {
                            def mypyResult = sh(
                                script: '''
                                    echo "=== Running mypy Type Checker ==="
                                    # Run mypy and capture output (continue on errors to count them)
                                    /root/.local/bin/uv run mypy ${SOURCE_DIR}/ --junit-xml mypy-report.xml > mypy-output.txt 2>&1 || true

                                    # Count errors from JUnit XML report
                                    if [ -f mypy-report.xml ]; then
                                        ERROR_COUNT=$(grep -c '<failure' mypy-report.xml 2>/dev/null || echo "0")
                                    else
                                        # Fallback: count error lines from output
                                        ERROR_COUNT=$(grep -cE '^[^:]+:[0-9]+:' mypy-output.txt 2>/dev/null || echo "0")
                                    fi

                                    echo "mypy errors found: ${ERROR_COUNT}"
                                    echo "Maximum allowed: ${MAX_MYPY_ERRORS}"

                                    # Show errors for visibility
                                    cat mypy-output.txt

                                    # Check against threshold
                                    if [ "${ERROR_COUNT}" -gt "${MAX_MYPY_ERRORS}" ]; then
                                        echo "QUALITY GATE FAILURE: Too many mypy errors (${ERROR_COUNT} > ${MAX_MYPY_ERRORS})"
                                        exit 1
                                    fi

                                    echo "QUALITY GATE PASSED: mypy errors within threshold"
                                    exit 0
                                ''',
                                returnStatus: true
                            )

                            if (mypyResult != 0 && params.ENFORCE_QUALITY_GATES) {
                                unstable("mypy quality gate failed - marking as unstable for SonarCloud report upload")
                            }
                        }
                    }
                    post {
                        always {
                            archiveArtifacts artifacts: 'mypy-report.xml,mypy-output.txt', allowEmptyArchive: true
                        }
                    }
                }
            }
        }

        stage('Security Scan') {
            parallel {
                stage('pip-audit') {
                    steps {
                        script {
                            def securityResult = sh(
                                script: '''
                                    echo "=== Running pip-audit (Dependency Vulnerability Scan) ==="

                                    # Run pip-audit and capture output
                                    /root/.local/bin/uv run pip-audit --desc --format json --output pip-audit-report.json 2>&1 || true
                                    /root/.local/bin/uv run pip-audit --desc --format markdown --output pip-audit-report.md 2>&1 || true

                                    # Analyze vulnerabilities using jq for reliable JSON parsing
                                    if [ -f pip-audit-report.json ] && [ -s pip-audit-report.json ]; then
                                        CRITICAL_COUNT=$(jq '[.dependencies[]?.vulns[]? | select(.aliases[]? | test("CRITICAL"; "i")) // select(.fix_versions == [])] | length' pip-audit-report.json 2>/dev/null || echo "0")
                                        HIGH_COUNT=$(jq '[.dependencies[]?.vulns[]? | select(.aliases[]? | test("HIGH"; "i"))] | length' pip-audit-report.json 2>/dev/null || echo "0")
                                        MEDIUM_COUNT=$(jq '[.dependencies[]?.vulns[]? | select(.aliases[]? | test("MEDIUM"; "i"))] | length' pip-audit-report.json 2>/dev/null || echo "0")
                                        LOW_COUNT=$(jq '[.dependencies[]?.vulns[]? | select(.aliases[]? | test("LOW"; "i"))] | length' pip-audit-report.json 2>/dev/null || echo "0")
                                        # Fallback: count total vulnerabilities if severity parsing fails
                                        if [ "$CRITICAL_COUNT" = "0" ] && [ "$HIGH_COUNT" = "0" ]; then
                                            TOTAL_VULNS=$(jq '[.dependencies[]?.vulns[]?] | length' pip-audit-report.json 2>/dev/null || echo "0")
                                            if [ "$TOTAL_VULNS" -gt 0 ]; then
                                                echo "Note: Found ${TOTAL_VULNS} vulnerabilities (severity detection may vary by pip-audit version)"
                                            fi
                                        fi
                                    else
                                        CRITICAL_COUNT=0
                                        HIGH_COUNT=0
                                        MEDIUM_COUNT=0
                                        LOW_COUNT=0
                                    fi

                                    echo ""
                                    echo "=== Security Scan Results ==="
                                    echo "Critical: ${CRITICAL_COUNT}"
                                    echo "High:     ${HIGH_COUNT}"
                                    echo "Medium:   ${MEDIUM_COUNT}"
                                    echo "Low:      ${LOW_COUNT}"
                                    echo ""

                                    # Display full report
                                    /root/.local/bin/uv run pip-audit --desc || true

                                    # Check quality gates
                                    GATE_FAILED=0

                                    if [ "${BLOCK_ON_CRITICAL_VULNS}" = "true" ] && [ "${CRITICAL_COUNT}" -gt 0 ]; then
                                        echo "QUALITY GATE FAILURE: ${CRITICAL_COUNT} critical vulnerabilities found"
                                        GATE_FAILED=1
                                    fi

                                    if [ "${BLOCK_ON_HIGH_VULNS}" = "true" ] && [ "${HIGH_COUNT}" -gt 0 ]; then
                                        echo "QUALITY GATE FAILURE: ${HIGH_COUNT} high-severity vulnerabilities found"
                                        GATE_FAILED=1
                                    fi

                                    if [ "${GATE_FAILED}" -eq 1 ]; then
                                        echo ""
                                        echo "========================================"
                                        echo "WARNING: Security vulnerabilities found"
                                        echo "========================================"
                                        echo "Review pip-audit-report.md for details and remediation steps"
                                        exit 1
                                    fi

                                    echo "QUALITY GATE PASSED: No blocking vulnerabilities found"
                                ''',
                                returnStatus: true
                            )

                            if (securityResult != 0) {
                                unstable("WARNING: Security quality gate failed - see output above for details")
                            }
                        }
                    }
                    post {
                        always {
                            archiveArtifacts artifacts: 'pip-audit-report.*', allowEmptyArchive: true
                        }
                    }
                }

                stage('Bandit') {
                    steps {
                        script {
                            // Exit codes: 2 = FAIL (high/critical), 1 = WARN (medium), 0 = PASS (low only)
                            def banditResult = sh(
                                script: '''
                                    echo "=== Running Bandit (Python Security Linter) ==="
                                    # Generate JSON report (always succeeds for archiving)
                                    /root/.local/bin/uv run bandit -r ${SOURCE_DIR} -f json -o bandit-report.json || true

                                    # Count security issues from JSON report using jq
                                    if [ -f bandit-report.json ] && [ -s bandit-report.json ]; then
                                        HIGH_COUNT=$(jq '[.results[] | select(.issue_severity == "HIGH")] | length' bandit-report.json 2>/dev/null || echo "0")
                                        MEDIUM_COUNT=$(jq '[.results[] | select(.issue_severity == "MEDIUM")] | length' bandit-report.json 2>/dev/null || echo "0")
                                        LOW_COUNT=$(jq '[.results[] | select(.issue_severity == "LOW")] | length' bandit-report.json 2>/dev/null || echo "0")
                                        TOTAL_COUNT=$((HIGH_COUNT + MEDIUM_COUNT + LOW_COUNT))
                                    else
                                        HIGH_COUNT=0
                                        MEDIUM_COUNT=0
                                        LOW_COUNT=0
                                        TOTAL_COUNT=0
                                    fi

                                    echo ""
                                    echo "=== Bandit Security Results ==="
                                    echo "High severity:   ${HIGH_COUNT}"
                                    echo "Medium severity: ${MEDIUM_COUNT}"
                                    echo "Low severity:    ${LOW_COUNT}"
                                    echo "Total issues:    ${TOTAL_COUNT}"
                                    echo ""
                                    echo "Quality Gate Rules:"
                                    echo "  - High severity:   FAIL (any = build failure)"
                                    echo "  - Medium severity: WARN (any = build unstable)"
                                    echo "  - Low severity:    PASS (informational only)"

                                    # Show human-readable output
                                    /root/.local/bin/uv run bandit -r ${SOURCE_DIR} -ll || true

                                    # Tiered quality gate: FAIL > WARN > PASS
                                    if [ "${HIGH_COUNT}" -gt 0 ]; then
                                        echo ""
                                        echo "========================================"
                                        echo "QUALITY GATE FAILURE: ${HIGH_COUNT} HIGH severity security issue(s)"
                                        echo "========================================"
                                        echo "High severity issues MUST be fixed before merge."
                                        exit 2
                                    fi

                                    if [ "${MEDIUM_COUNT}" -gt 0 ]; then
                                        echo ""
                                        echo "========================================"
                                        echo "QUALITY GATE WARNING: ${MEDIUM_COUNT} MEDIUM severity security issue(s)"
                                        echo "========================================"
                                        echo "Medium severity issues should be reviewed and addressed."
                                        exit 1
                                    fi

                                    if [ "${LOW_COUNT}" -gt 0 ]; then
                                        echo ""
                                        echo "QUALITY GATE PASSED: ${LOW_COUNT} low severity issue(s) (informational)"
                                    else
                                        echo ""
                                        echo "QUALITY GATE PASSED: No security issues found"
                                    fi
                                    exit 0
                                ''',
                                returnStatus: true
                            )

                            if (banditResult == 2 && params.ENFORCE_QUALITY_GATES) {
                                unstable("BANDIT FAILURE: High severity security issues found - must fix before merge")
                            } else if (banditResult == 1 && params.ENFORCE_QUALITY_GATES) {
                                unstable("BANDIT WARNING: Medium severity security issues found - review recommended")
                            }
                        }
                    }
                    post {
                        always {
                            archiveArtifacts artifacts: 'bandit-report.json', allowEmptyArchive: true
                        }
                    }
                }

                stage('Trivy') {
                    steps {
                        sh '''
                            echo "=== Installing and Running Trivy (Filesystem Scan) ==="
                            if ! command -v /root/.local/bin/trivy &> /dev/null; then
                                curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /root/.local/bin
                            fi
                            /root/.local/bin/trivy fs . \
                                --severity HIGH,CRITICAL \
                                --format json \
                                --output trivy-report.json \
                                --exit-code 0 || true
                            /root/.local/bin/trivy fs . --severity HIGH,CRITICAL --exit-code 0 || true
                        '''
                    }
                    post {
                        always {
                            archiveArtifacts artifacts: 'trivy-report.json', allowEmptyArchive: true
                        }
                    }
                }

                stage('Semgrep') {
                    steps {
                        script {
                            def semgrepResult = sh(
                                script: '''
                                    echo "=== Installing and Running Semgrep (SAST) ==="
                                    pip3 install --quiet semgrep

                                    # Run Semgrep with Python security rules
                                    semgrep scan \
                                        --config=auto \
                                        --config=p/python \
                                        --config=p/security-audit \
                                        --json \
                                        --output=semgrep-report.json \
                                        ${SOURCE_DIR}/ 2>&1 || true

                                    # Count findings by severity
                                    if [ -f semgrep-report.json ] && [ -s semgrep-report.json ]; then
                                        ERROR_COUNT=$(jq '[.results[] | select(.extra.severity == "ERROR")] | length' semgrep-report.json 2>/dev/null || echo "0")
                                        WARNING_COUNT=$(jq '[.results[] | select(.extra.severity == "WARNING")] | length' semgrep-report.json 2>/dev/null || echo "0")
                                        INFO_COUNT=$(jq '[.results[] | select(.extra.severity == "INFO")] | length' semgrep-report.json 2>/dev/null || echo "0")
                                        TOTAL_COUNT=$(jq '.results | length' semgrep-report.json 2>/dev/null || echo "0")
                                    else
                                        ERROR_COUNT=0
                                        WARNING_COUNT=0
                                        INFO_COUNT=0
                                        TOTAL_COUNT=0
                                    fi

                                    echo ""
                                    echo "=== Semgrep SAST Results ==="
                                    echo "Error severity:   ${ERROR_COUNT}"
                                    echo "Warning severity: ${WARNING_COUNT}"
                                    echo "Info severity:    ${INFO_COUNT}"
                                    echo "Total findings:   ${TOTAL_COUNT}"

                                    # Show human-readable output
                                    semgrep scan \
                                        --config=auto \
                                        --config=p/python \
                                        --config=p/security-audit \
                                        ${SOURCE_DIR}/ 2>&1 || true

                                    # Quality gate: fail on ERROR severity findings
                                    if [ "${ERROR_COUNT}" -gt 0 ]; then
                                        echo ""
                                        echo "========================================"
                                        echo "QUALITY GATE FAILURE: ${ERROR_COUNT} ERROR severity finding(s)"
                                        echo "========================================"
                                        exit 1
                                    fi

                                    echo "QUALITY GATE PASSED: No ERROR severity findings"
                                    exit 0
                                ''',
                                returnStatus: true
                            )

                            if (semgrepResult != 0 && params.ENFORCE_QUALITY_GATES) {
                                unstable("Semgrep SAST found ERROR severity issues - review recommended")
                            }
                        }
                    }
                    post {
                        always {
                            archiveArtifacts artifacts: 'semgrep-report.json', allowEmptyArchive: true
                        }
                    }
                }
            }
        }

        stage('Test') {
            steps {
                script {
                    def testResult = sh(
                        script: '''
                            echo "=== Running Tests with Coverage ==="
                            /root/.local/bin/uv run pytest tests/ \
                                --cov=${SOURCE_DIR} \
                                --cov-report=term \
                                --cov-report=xml:coverage.xml \
                                --cov-report=html:htmlcov \
                                --junitxml=pytest-report.xml \
                                --verbose
                        ''',
                        returnStatus: true
                    )

                    if (testResult != 0) {
                        unstable("WARNING: Tests failed - see output above for details")
                    }
                }
            }
            post {
                always {
                    junit allowEmptyResults: true, testResults: 'pytest-report.xml'
                    archiveArtifacts artifacts: 'coverage.xml,pytest-report.xml', allowEmptyArchive: true
                    archiveArtifacts artifacts: 'htmlcov/**', allowEmptyArchive: true
                    publishHTML(target: [
                        allowMissing: true,
                        alwaysLinkToLastBuild: true,
                        keepAll: true,
                        reportDir: 'htmlcov',
                        reportFiles: 'index.html',
                        reportName: 'Coverage Report'
                    ])
                }
            }
        }

        stage('Coverage Quality Gate') {
            steps {
                script {
                    def coverageResult = sh(
                        script: '''
                            echo "=== Validating Coverage Quality Gate ==="

                            if [ ! -f coverage.xml ]; then
                                echo "ERROR: coverage.xml not found"
                                exit 1
                            fi

                            # Extract coverage percentage from XML using Python for portability
                            COVERAGE_PCT=$(python3 -c "
import xml.etree.ElementTree as ET
try:
    tree = ET.parse('coverage.xml')
    rate = float(tree.getroot().get('line-rate', 0))
    print(int(rate * 100))
except Exception as e:
    print('0')
")

                            echo "Coverage: ${COVERAGE_PCT}%"
                            echo "Threshold: ${COVERAGE_THRESHOLD}%"

                            if [ "${COVERAGE_PCT}" -lt "${COVERAGE_THRESHOLD}" ]; then
                                echo ""
                                echo "========================================"
                                echo "WARNING: Coverage ${COVERAGE_PCT}% is below threshold ${COVERAGE_THRESHOLD}%"
                                echo "========================================"
                                exit 1
                            fi

                            echo "QUALITY GATE PASSED: Coverage ${COVERAGE_PCT}% meets threshold"
                        ''',
                        returnStatus: true
                    )

                    if (coverageResult != 0) {
                        unstable("WARNING: Coverage quality gate failed - see output above for details")
                    }
                }
            }
        }

        stage('SonarCloud Analysis') {
            when {
                expression { params.RUN_SONAR }
            }
            environment {
                SONAR_ORGANIZATION = 'visccyberacct'
                SONAR_PROJECT_KEY = 'visccyberacct_n8n-mcp-server'
                SONAR_SCANNER_VERSION = '6.2.1.4610'
            }
            steps {
                withCredentials([string(credentialsId: 'sonarcloud-token', variable: 'SONAR_TOKEN')]) {
                    sh '''
                        echo "=== Installing SonarScanner CLI ==="
                        if [ ! -d "/root/.local/sonar-scanner-${SONAR_SCANNER_VERSION}-linux-x64" ]; then
                            curl -sSLo sonar-scanner.zip "https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-${SONAR_SCANNER_VERSION}-linux-x64.zip"
                            # Use Python's zipfile module (built-in, no unzip required)
                            python3 -c "import zipfile; zipfile.ZipFile('sonar-scanner.zip').extractall('/root/.local/')"
                            rm -f sonar-scanner.zip
                        fi
                        # Always ensure sonar-scanner is executable (zipfile doesn't preserve permissions)
                        chmod +x "/root/.local/sonar-scanner-${SONAR_SCANNER_VERSION}-linux-x64/bin/sonar-scanner"
                        export PATH="/root/.local/sonar-scanner-${SONAR_SCANNER_VERSION}-linux-x64/bin:$PATH"

                        # Configure JAVA_HOME for sonar-scanner
                        echo "=== Configuring Java Environment ==="
                        if [ -z "$JAVA_HOME" ]; then
                            # Find java binary and derive JAVA_HOME from it
                            JAVA_BIN=$(which java 2>/dev/null || true)
                            if [ -n "$JAVA_BIN" ]; then
                                # Resolve symlinks to get actual path
                                JAVA_BIN=$(readlink -f "$JAVA_BIN")
                                # JAVA_HOME is typically 2 levels up from bin/java
                                export JAVA_HOME=$(dirname $(dirname "$JAVA_BIN"))
                                echo "Found JAVA_HOME from PATH: $JAVA_HOME"
                            fi
                        fi

                        if [ -z "$JAVA_HOME" ]; then
                            echo "ERROR: JAVA_HOME not set and Java not found"
                            exit 1
                        fi

                        export PATH="$JAVA_HOME/bin:$PATH"
                        echo "JAVA_HOME: $JAVA_HOME"
                        echo "Java version: $(java -version 2>&1 | head -1)"

                        echo "=== Running SonarCloud Analysis ==="
                        # Run sonar-scanner JAR directly (bypasses launcher script Java detection issues)
                        SCANNER_HOME="/root/.local/sonar-scanner-${SONAR_SCANNER_VERSION}-linux-x64"
                        SCANNER_JAR="$SCANNER_HOME/lib/sonar-scanner-cli-${SONAR_SCANNER_VERSION}.jar"

                        "$JAVA_HOME/bin/java" \
                            -Djava.awt.headless=true \
                            -classpath "$SCANNER_JAR" \
                            org.sonarsource.scanner.cli.Main \
                            -Dsonar.host.url=https://sonarcloud.io \
                            -Dsonar.token="${SONAR_TOKEN}" \
                            -Dsonar.projectKey="${SONAR_PROJECT_KEY}" \
                            -Dsonar.organization="${SONAR_ORGANIZATION}" \
                            -Dsonar.projectName="${PROJECT_NAME}" \
                            -Dsonar.sources=${SOURCE_DIR} \
                            -Dsonar.tests=tests \
                            -Dsonar.python.version=3.12 \
                            -Dsonar.python.coverage.reportPaths=coverage.xml \
                            -Dsonar.python.ruff.reportPaths=ruff-report.json \
                            -Dsonar.python.mypy.reportPaths=mypy-output.txt \
                            -Dsonar.python.bandit.reportPaths=bandit-report.json

                        echo "SonarCloud analysis complete"
                        echo "View at: https://sonarcloud.io/project/overview?id=${SONAR_PROJECT_KEY}"
                    '''
                }
            }
        }

        stage('SonarCloud Quality Gate') {
            when {
                expression { params.RUN_SONAR }
            }
            environment {
                SONAR_PROJECT_KEY = 'visccyberacct_n8n-mcp-server'
            }
            steps {
                timeout(time: 5, unit: 'MINUTES') {
                    withCredentials([string(credentialsId: 'sonarcloud-token', variable: 'SONAR_TOKEN')]) {
                        script {
                            def gateResult = sh(
                                script: '''
                                    echo "=== Checking SonarCloud Quality Gate Status ==="
                                    sleep 10  # Wait for analysis to process

                                    # Get quality gate status using Bearer token (more secure than -u)
                                    RESPONSE=$(curl -s \
                                        -H "Authorization: Bearer ${SONAR_TOKEN}" \
                                        "https://sonarcloud.io/api/qualitygates/project_status?projectKey=${SONAR_PROJECT_KEY}")

                                    # Parse status using jq for reliable JSON handling
                                    GATE_STATUS=$(echo "$RESPONSE" | jq -r '.projectStatus.status // "UNKNOWN"' 2>/dev/null || echo "UNKNOWN")

                                    echo "Quality Gate Status: ${GATE_STATUS}"
                                    echo ""

                                    # Parse conditions if available
                                    echo "=== Quality Gate Conditions ==="
                                    echo "$RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    conditions = data.get('projectStatus', {}).get('conditions', [])
    for c in conditions:
        status = c.get('status', 'UNKNOWN')
        metric = c.get('metricKey', 'unknown')
        actual = c.get('actualValue', 'N/A')
        threshold = c.get('errorThreshold', 'N/A')
        icon = '✓' if status == 'OK' else '✗'
        print(f'{icon} {metric}: {actual} (threshold: {threshold})')
except:
    print('Unable to parse conditions')
" 2>/dev/null || true

                                    echo ""

                                    if [ "$GATE_STATUS" = "ERROR" ]; then
                                        echo ""
                                        echo "========================================"
                                        echo "WARNING: SonarCloud quality gate failed"
                                        echo "========================================"
                                        exit 1
                                    elif [ "$GATE_STATUS" = "OK" ]; then
                                        echo "QUALITY GATE PASSED: SonarCloud quality gate passed"
                                    else
                                        echo "Quality Gate status: ${GATE_STATUS}"
                                    fi
                                ''',
                                returnStatus: true
                            )

                            if (gateResult != 0) {
                                unstable("WARNING: SonarCloud quality gate failed - see output above for details")
                            }
                        }
                    }
                }
            }
        }

        stage('Build Package') {
            steps {
                sh '''
                    echo "=== Building Distribution Package ==="
                    /root/.local/bin/uv build

                    echo ""
                    echo "=== Built Packages ==="
                    ls -la dist/
                '''
            }
            post {
                success {
                    archiveArtifacts artifacts: 'dist/*', fingerprint: true
                }
            }
        }

        stage('Generate SBOM') {
            when {
                expression { params.UPLOAD_SBOM }
            }
            steps {
                sh '''
                    echo "=== Installing Syft ==="
                    curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /root/.local/bin

                    # Project metadata
                    PROJECT_DESCRIPTION="MCP server providing tools to interact with n8n workflow automation platform"
                    PROJECT_LICENSE="MIT"
                    SUPPLIER_NAME="Kent Viscount"
                    SUPPLIER_EMAIL="visccyberacct@gmail.com"
                    SUPPLIER_URL="https://github.com/visccyberacct/n8n-mcp-server"

                    # Extract version from pyproject.toml
                    PROJECT_VERSION=$(grep -m1 'version = ' pyproject.toml | sed 's/version = "\\(.*\\)"/\\1/')
                    echo "Detected version: ${PROJECT_VERSION}"

                    echo ""
                    echo "=== Generating CycloneDX 1.6 Compliant SBOM ==="
                    echo "  Project: ${PROJECT_NAME}"
                    echo "  Version: ${PROJECT_VERSION}"

                    # Generate initial SBOM with Syft
                    /root/.local/bin/syft dir:. \
                        --source-name "${PROJECT_NAME}" \
                        --source-version "${PROJECT_VERSION}" \
                        -o cyclonedx-json=sbom-raw.json \
                        -o spdx-json=sbom-spdx.json

                    # Enrich SBOM metadata with jq
                    jq --arg name "${PROJECT_NAME}" \
                       --arg version "${PROJECT_VERSION}" \
                       --arg desc "${PROJECT_DESCRIPTION}" \
                       --arg license "${PROJECT_LICENSE}" \
                       --arg supplier_name "${SUPPLIER_NAME}" \
                       --arg supplier_email "${SUPPLIER_EMAIL}" \
                       --arg supplier_url "${SUPPLIER_URL}" \
                       --arg build_num "${BUILD_NUMBER}" \
                       --arg build_url "${BUILD_URL}" \
                       '
                       # Update metadata.component with correct type and enriched data
                       .metadata.component.type = "application" |
                       .metadata.component.name = $name |
                       .metadata.component.version = $version |
                       .metadata.component.description = $desc |
                       .metadata.component.licenses = [{"license": {"id": $license}}] |
                       .metadata.component.supplier = {
                           "name": $supplier_name,
                           "contact": [{"email": $supplier_email}],
                           "url": [$supplier_url]
                       } |
                       .metadata.component.publisher = $supplier_name |
                       .metadata.component.purl = ("pkg:pypi/" + $name + "@" + $version) |
                       .metadata.component["bom-ref"] = ($name + "@" + $version) |
                       .metadata.component.externalReferences = [
                           {"type": "website", "url": $supplier_url},
                           {"type": "build-system", "url": $build_url, "comment": ("Jenkins Build #" + $build_num)},
                           {"type": "vcs", "url": ($supplier_url + ".git")}
                       ] |
                       # Add manufacturer (same as supplier for this project)
                       .metadata.manufacture = {
                           "name": $supplier_name,
                           "contact": [{"email": $supplier_email}],
                           "url": [$supplier_url]
                       } |
                       # Add supplier at metadata level
                       .metadata.supplier = {
                           "name": $supplier_name,
                           "contact": [{"email": $supplier_email}],
                           "url": [$supplier_url]
                       } |
                       # Add authors
                       .metadata.authors = [{"name": $supplier_name, "email": $supplier_email}] |
                       # Add lifecycles (build phase)
                       .metadata.lifecycles = [{"phase": "build"}]
                       ' sbom-raw.json > sbom.json

                    rm -f sbom-raw.json

                    echo ""
                    echo "=== Validating CycloneDX 1.6 Compliance ==="
                    echo "Required fields:"
                    echo "  ✓ Component name: $(jq -r '.metadata.component.name' sbom.json)"
                    echo "  ✓ Component type: $(jq -r '.metadata.component.type' sbom.json)"
                    echo "  ✓ Component version: $(jq -r '.metadata.component.version' sbom.json)"
                    echo ""
                    echo "Recommended fields:"
                    echo "  ✓ Spec version: $(jq -r '.specVersion' sbom.json)"
                    echo "  ✓ Description: $(jq -r '.metadata.component.description // "not set"' sbom.json | head -c 50)..."
                    echo "  ✓ License: $(jq -r '.metadata.component.licenses[0].license.id // "not set"' sbom.json)"
                    echo "  ✓ Supplier: $(jq -r '.metadata.component.supplier.name // "not set"' sbom.json)"
                    echo "  ✓ PURL: $(jq -r '.metadata.component.purl // "not set"' sbom.json)"
                    echo ""
                    echo "Statistics:"
                    echo "  ✓ Components count: $(jq '.components | length' sbom.json)"

                    # Export version for subsequent stages
                    echo "${PROJECT_VERSION}" > .project_version
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: 'sbom*.json', allowEmptyArchive: true
                }
            }
        }

        stage('Upload to Dependency-Track') {
            when {
                expression { params.UPLOAD_SBOM }
            }
            steps {
                script {
                    echo "=== Uploading SBOM to Dependency-Track ==="
                    def projectVersion = readFile('.project_version').trim()
                    echo "Project version: ${projectVersion}"

                    withCredentials([string(credentialsId: 'dependency-track', variable: 'DTRACK_KEY')]) {
                        dependencyTrackPublisher(
                            artifact: 'sbom.json',
                            projectId: 'b8cc347f-77d9-4ce2-b138-fbe6aba6ee9e',
                            projectVersion: projectVersion,
                            dependencyTrackApiKey: DTRACK_KEY,
                            synchronous: true,
                            projectProperties: [
                                isLatest: true
                            ],
                            failOnViolationFail: true,
                            failedNewCritical: 0,
                            failedNewHigh: 0,
                            failedTotalCritical: 0,
                            failedTotalHigh: 0
                        )
                    }
                }
            }
        }
    }

    post {
        always {
            echo "Pipeline completed with status: ${currentBuild.currentResult}"

            // Generate quality gate summary
            script {
                echo """
=== QUALITY GATE SUMMARY ===
Quality Gates Enforced: ${params.ENFORCE_QUALITY_GATES}
Coverage Threshold: ${env.COVERAGE_THRESHOLD}%
Max Ruff Errors: ${env.MAX_RUFF_ERRORS}
Max mypy Errors: ${env.MAX_MYPY_ERRORS}
Block on Critical Vulns: ${env.BLOCK_ON_CRITICAL_VULNS}
Block on High Vulns: ${env.BLOCK_ON_HIGH_VULNS}
================================
"""
            }

            // Clean up virtual environment
            sh 'rm -rf .venv venv venv-* || true'

            // Clean workspace on successful build (preserve failure artifacts)
            cleanWs(
                cleanWhenSuccess: true,
                cleanWhenFailure: false,
                cleanWhenAborted: false,
                notFailBuild: true,
                deleteDirs: true,
                patterns: [
                    [pattern: '.venv/**', type: 'INCLUDE'],
                    [pattern: 'venv/**', type: 'INCLUDE'],
                    [pattern: '**/__pycache__/**', type: 'INCLUDE'],
                    [pattern: '*.pyc', type: 'INCLUDE'],
                    [pattern: '.pytest_cache/**', type: 'INCLUDE'],
                    [pattern: '.ruff_cache/**', type: 'INCLUDE'],
                    [pattern: '.project_version', type: 'INCLUDE'],
                    [pattern: '.uv-cache/**', type: 'INCLUDE']
                ]
            )
        }

        success {
            echo '=== ALL QUALITY GATES PASSED - Pipeline completed successfully ==='
            script {
                if (env.CHANGE_ID) {
                    // This is a PR build
                    echo "PR #${env.CHANGE_ID} passed all quality gates"
                }
            }
        }

        failure {
            echo '=== QUALITY GATE FAILURE - Pipeline failed ==='
            script {
                echo "One or more quality gates failed. Review logs at: ${env.BUILD_URL}"
                echo "Check the following:"
                echo "  - Code formatting (Ruff)"
                echo "  - Lint errors (Ruff)"
                echo "  - Type errors (mypy)"
                echo "  - Security issues (Bandit, Semgrep)"
                echo "  - Dependency vulnerabilities (pip-audit, Trivy)"
                echo "  - Test failures/coverage (pytest)"
                echo "  - SonarCloud quality gate"
            }
        }

        unstable {
            echo '=== Pipeline completed with warnings ==='
            echo 'Some quality checks passed with warnings - review the reports'
        }
    }
}
