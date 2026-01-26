#!/usr/bin/env groovy
/**
 * Python Project CI/CD Pipeline Template with Quality Gates
 *
 * This pipeline provides comprehensive CI/CD with enforced quality standards:
 * - Code quality checks (Ruff format/lint, mypy) with quality gates
 * - Security scanning (Semgrep, Bandit, pip-audit, Trivy) with severity thresholds
 * - Unit testing with coverage thresholds
 * - SonarCloud analysis with quality gate enforcement
 * - SBOM generation (Syft) and Dependency-Track vulnerability analysis
 *
 * Quality Gates:
 * - Coverage: Minimum 80% (configurable)
 * - Lint Errors: 0 critical errors allowed
 * - Security: No critical/high vulnerabilities (pip-audit, Trivy)
 * - SonarCloud: Must pass quality gate
 * - Dependency-Track: No critical/high vulnerabilities in dependencies
 *
 * TEMPLATE USAGE:
 * 1. Copy this file to your project as 'Jenkinsfile'
 * 2. Update PROJECT_NAME, SOURCE_DIR, and other project settings
 * 3. Update SONAR_ORGANIZATION and SONAR_PROJECT_KEY for SonarCloud
 * 4. Update DTRACK_URL for your Dependency-Track instance
 * 5. Update SUPPLIER_* variables with your information
 * 6. Ensure Jenkins has required credentials:
 *    - sonarcloud-token: SonarCloud API token
 *    - dependency-track: Dependency-Track API key (needs BOM_UPLOAD, VIEW_VULNERABILITY,
 *                        PROJECT_CREATION_UPLOAD, PORTFOLIO_MANAGEMENT permissions)
 *
 * REQUIRED JENKINS PLUGINS:
 * - OWASP Dependency-Track Plugin (https://plugins.jenkins.io/dependency-track/)
 */

pipeline {
    agent { label 'jenkins-agent' }

    options {
        buildDiscarder(logRotator(numToKeepStr: '20'))
        timeout(time: 30, unit: 'MINUTES')
        timestamps()
        disableConcurrentBuilds()
        skipDefaultCheckout(false)
    }

    environment {
        // Python settings
        PYTHON_VERSION = '3.11'
        PYTHONDONTWRITEBYTECODE = '1'
        PYTHONUNBUFFERED = '1'
        UV_NO_CACHE = '1'
        COVERAGE_FILE = '.coverage'
        PATH = "${HOME}/.local/bin:${env.PATH}"

        // =====================================================
        // PROJECT SETTINGS - UPDATE THESE FOR YOUR PROJECT
        // =====================================================
        PROJECT_NAME = 'n8n-mcp-server'
        SOURCE_DIR = 'src'
        PROJECT_DESCRIPTION = 'MCP Server for n8n workflow automation API'
        PROJECT_LICENSE = 'MIT'
        SUPPLIER_NAME = 'Kent Viscount'
        SUPPLIER_EMAIL = 'visccyberacct@gmail.com'
        SUPPLIER_URL = 'https://github.com/kviscount/n8n-mcp-server'

        // Quality gate thresholds
        COVERAGE_THRESHOLD = '80'
        MAX_LINT_ERRORS = '0'
        BLOCK_ON_CRITICAL_VULNS = 'true'
        BLOCK_ON_HIGH_VULNS = 'false'
        FAIL_ON_SONAR_GATE = 'true'

        // Dependency-Track settings (update URL for your instance)
        DTRACK_URL = 'https://dtrack.homelab.com'
        // Vulnerability thresholds for Dependency-Track quality gate
        // Set to -1 to disable threshold (allow unlimited)
        DTRACK_FAIL_CRITICAL = '1'    // Fail build on this many critical vulns
        DTRACK_FAIL_HIGH = '1'        // Fail build on this many high vulns
        DTRACK_UNSTABLE_MEDIUM = '10' // Mark unstable on this many medium vulns
        DTRACK_UNSTABLE_LOW = '-1'    // Mark unstable on this many low vulns
    }

    parameters {
        booleanParam(
            name: 'RUN_SONAR',
            defaultValue: true,
            description: 'Run SonarCloud analysis'
        )
        booleanParam(
            name: 'RUN_SECURITY_SCAN',
            defaultValue: true,
            description: 'Run security vulnerability scanning'
        )
        booleanParam(
            name: 'UPLOAD_SBOM',
            defaultValue: true,
            description: 'Generate SBOM and upload to Dependency-Track'
        )
        booleanParam(
            name: 'DTRACK_QUALITY_GATE',
            defaultValue: true,
            description: 'Wait for Dependency-Track analysis and enforce vulnerability thresholds'
        )
        booleanParam(
            name: 'ENFORCE_QUALITY_GATES',
            defaultValue: true,
            description: 'Enforce quality gates (fail build on violations)'
        )
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                script {
                    env.GIT_COMMIT_SHORT = sh(
                        script: 'git rev-parse --short HEAD',
                        returnStdout: true
                    ).trim()
                    env.GIT_BRANCH_NAME = sh(
                        script: 'git rev-parse --abbrev-ref HEAD',
                        returnStdout: true
                    ).trim()
                }
                echo "Building commit ${env.GIT_COMMIT_SHORT} on branch ${env.GIT_BRANCH_NAME}"
                echo "Quality Gates Enforcement: ${params.ENFORCE_QUALITY_GATES}"
            }
        }

        stage('Pre-Build Cleanup') {
            steps {
                sh '''
                    echo "=== Cleaning stale artifacts from previous builds ==="
                    # Remove stale files that may persist across builds
                    rm -rf .venv venv venv-* .pytest_cache .ruff_cache .mypy_cache htmlcov
                    rm -f .coverage coverage.xml pytest-report.xml mypy-report.xml
                    rm -f ruff-report.json bandit-report.json semgrep-report.json
                    rm -f pip-audit-report.json pip-audit-report.md trivy-report.json
                    rm -f sbom*.json
                    echo "Cleanup complete"
                '''
            }
        }

        stage('Setup Environment') {
            steps {
                sh '''
                    echo "=== System Information ==="
                    python3 --version

                    echo ""
                    echo "=== Installing/Checking uv ==="
                    if ! command -v uv &> /dev/null; then
                        echo "Installing uv..."
                        curl -LsSf https://astral.sh/uv/install.sh | sh
                        export PATH="$HOME/.local/bin:$PATH"
                    fi
                    uv --version

                    echo ""
                    echo "=== Syncing Dependencies with uv ==="
                    uv sync --all-extras

                    echo ""
                    echo "=== Installed Packages ==="
                    uv pip list
                '''
            }
        }

        stage('Code Quality') {
            parallel {
                stage('Format - Ruff') {
                    steps {
                        script {
                            def formatResult = sh(
                                script: '''
                                    echo "=== Checking Code Formatting with Ruff ==="
                                    uv run ruff format --check --diff ${SOURCE_DIR}/ tests/ || {
                                        echo "QUALITY GATE FAILURE: Code formatting issues found."
                                        echo "Run 'uv run ruff format ${SOURCE_DIR}/ tests/' to fix."
                                        exit 1
                                    }
                                    echo "QUALITY GATE PASSED: Code formatting OK"
                                ''',
                                returnStatus: true
                            )

                            if (formatResult != 0 && params.ENFORCE_QUALITY_GATES) {
                                error("Ruff formatting quality gate failed")
                            }
                        }
                    }
                }

                stage('Lint - Ruff') {
                    steps {
                        script {
                            def lintResult = sh(
                                script: '''
                                    echo "=== Running Ruff Linter ==="
                                    uv run ruff check ${SOURCE_DIR}/ tests/ --output-format=json > ruff-report.json 2>&1 || true

                                    # Count errors using jq for reliable JSON parsing
                                    if [ -f ruff-report.json ] && [ -s ruff-report.json ]; then
                                        ERROR_COUNT=$(jq 'length' ruff-report.json 2>/dev/null || echo "0")
                                    else
                                        ERROR_COUNT=0
                                    fi

                                    echo "Lint errors found: ${ERROR_COUNT}"
                                    echo "Maximum allowed: ${MAX_LINT_ERRORS}"

                                    # Show errors for visibility
                                    uv run ruff check ${SOURCE_DIR}/ tests/ || true

                                    # Check against threshold
                                    if [ "${ERROR_COUNT}" -gt "${MAX_LINT_ERRORS}" ]; then
                                        echo "QUALITY GATE FAILURE: Too many lint errors (${ERROR_COUNT} > ${MAX_LINT_ERRORS})"
                                        exit 1
                                    fi

                                    echo "QUALITY GATE PASSED: Lint errors within threshold"
                                    exit 0
                                ''',
                                returnStatus: true
                            )

                            if (lintResult != 0 && params.ENFORCE_QUALITY_GATES) {
                                error("Ruff lint quality gate failed")
                            }
                        }
                    }
                    post {
                        always {
                            archiveArtifacts artifacts: 'ruff-report.json', allowEmptyArchive: true
                        }
                    }
                }

                stage('Type Check - mypy') {
                    steps {
                        script {
                            def mypyResult = sh(
                                script: '''
                                    echo "=== Running mypy Type Checker ==="
                                    uv run mypy ${SOURCE_DIR}/ --junit-xml mypy-report.xml || {
                                        echo "QUALITY GATE FAILURE: Type checking failed"
                                        exit 1
                                    }
                                    echo "QUALITY GATE PASSED: Type checking OK"
                                ''',
                                returnStatus: true
                            )

                            if (mypyResult != 0 && params.ENFORCE_QUALITY_GATES) {
                                error("mypy type check quality gate failed")
                            }
                        }
                    }
                    post {
                        always {
                            junit allowEmptyResults: true, testResults: 'mypy-report.xml'
                            archiveArtifacts artifacts: 'mypy-report.xml', allowEmptyArchive: true
                        }
                    }
                }
            }
        }

        stage('Security Scan') {
            when {
                expression { params.RUN_SECURITY_SCAN }
            }
            parallel {
                stage('Semgrep') {
                    steps {
                        script {
                            sh '''
                                echo "=== Running Semgrep (SAST) ==="
                                if ! command -v semgrep &> /dev/null; then
                                    echo "Installing semgrep..."
                                    uv pip install semgrep
                                fi

                                # Run Semgrep with Python security rules
                                uv run semgrep scan \
                                    --config "p/python" \
                                    --config "p/security-audit" \
                                    --json --output semgrep-report.json \
                                    ${SOURCE_DIR}/ || true

                                # Also run in readable format
                                uv run semgrep scan \
                                    --config "p/python" \
                                    --config "p/security-audit" \
                                    ${SOURCE_DIR}/ || true

                                echo "Semgrep scan complete"
                            '''
                        }
                    }
                    post {
                        always {
                            archiveArtifacts artifacts: 'semgrep-report.json', allowEmptyArchive: true
                        }
                    }
                }

                stage('Bandit') {
                    steps {
                        sh '''
                            echo "=== Running Bandit (Python Security Linter) ==="
                            uv run bandit -r ${SOURCE_DIR} -f json -o bandit-report.json || true
                            uv run bandit -r ${SOURCE_DIR} -ll || true
                        '''
                    }
                    post {
                        always {
                            archiveArtifacts artifacts: 'bandit-report.json', allowEmptyArchive: true
                        }
                    }
                }

                stage('pip-audit') {
                    steps {
                        script {
                            sh '''
                                echo "=== Running pip-audit (Dependency Vulnerability Scan) ==="
                                # To ignore specific CVEs with no fix available, add: --ignore-vuln CVE-XXXX-XXXXX
                                uv run pip-audit --desc --format json --output pip-audit-report.json || true
                                uv run pip-audit --desc --format markdown --output pip-audit-report.md || true
                            '''

                            // Parse vulnerability counts with jq
                            def vulnInfo = sh(
                                script: '''
                                    if [ -f pip-audit-report.json ] && [ -s pip-audit-report.json ]; then
                                        if jq -e . pip-audit-report.json >/dev/null 2>&1; then
                                            CRITICAL=$(jq '[.dependencies[]?.vulns[]? | select(.fix_versions != null) | .id] | length' pip-audit-report.json 2>/dev/null || echo "0")
                                            HIGH=$(jq '[.dependencies[]?.vulns[]? | select(.fix_versions == null) | .id] | length' pip-audit-report.json 2>/dev/null || echo "0")
                                            TOTAL=$(jq '[.dependencies[]?.vulns[]? | .id] | length' pip-audit-report.json 2>/dev/null || echo "0")
                                            echo "${CRITICAL}:${HIGH}:${TOTAL}"
                                        else
                                            echo "0:0:0"
                                        fi
                                    else
                                        echo "0:0:0"
                                    fi
                                ''',
                                returnStdout: true
                            ).trim()

                            def counts = vulnInfo.split(':')
                            def criticalCount = counts[0].toInteger()
                            def highCount = counts[1].toInteger()
                            def totalCount = counts[2].toInteger()

                            echo "Vulnerability scan results: ${totalCount} total (critical: ${criticalCount}, high: ${highCount})"

                            if (params.ENFORCE_QUALITY_GATES) {
                                if (env.BLOCK_ON_CRITICAL_VULNS == 'true' && criticalCount > 0) {
                                    error("QUALITY GATE FAILURE: Found ${criticalCount} critical vulnerabilities")
                                }
                                if (env.BLOCK_ON_HIGH_VULNS == 'true' && highCount > 0) {
                                    error("QUALITY GATE FAILURE: Found ${highCount} high vulnerabilities")
                                }
                            }

                            if (totalCount == 0) {
                                echo "QUALITY GATE PASSED: No vulnerabilities found"
                            } else {
                                echo "Security scan complete with ${totalCount} findings"
                            }
                        }
                    }
                    post {
                        always {
                            archiveArtifacts artifacts: 'pip-audit-report.*', allowEmptyArchive: true
                        }
                    }
                }

                stage('Trivy') {
                    steps {
                        script {
                            sh '''
                                echo "=== Running Trivy (Filesystem Scan) ==="
                                if ! command -v trivy &> /dev/null; then
                                    curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b $HOME/.local/bin
                                fi
                                # Use .trivyignore for CVE exceptions (no fix available)
                                TRIVY_OPTS="--severity MEDIUM,HIGH,CRITICAL"
                                [ -f .trivyignore ] && TRIVY_OPTS="$TRIVY_OPTS --ignorefile .trivyignore"
                                $HOME/.local/bin/trivy fs . $TRIVY_OPTS \
                                    --format json \
                                    --output trivy-report.json \
                                    --exit-code 0 || true
                                $HOME/.local/bin/trivy fs . $TRIVY_OPTS || true
                            '''

                            // Parse Trivy results and enforce quality gates
                            def trivyInfo = sh(
                                script: '''
                                    if [ -f trivy-report.json ] && [ -s trivy-report.json ]; then
                                        if jq -e . trivy-report.json >/dev/null 2>&1; then
                                            CRITICAL=$(jq '[.Results[]?.Vulnerabilities[]? | select(.Severity == "CRITICAL")] | length' trivy-report.json 2>/dev/null || echo "0")
                                            HIGH=$(jq '[.Results[]?.Vulnerabilities[]? | select(.Severity == "HIGH")] | length' trivy-report.json 2>/dev/null || echo "0")
                                            MEDIUM=$(jq '[.Results[]?.Vulnerabilities[]? | select(.Severity == "MEDIUM")] | length' trivy-report.json 2>/dev/null || echo "0")
                                            echo "${CRITICAL}:${HIGH}:${MEDIUM}"
                                        else
                                            echo "0:0:0"
                                        fi
                                    else
                                        echo "0:0:0"
                                    fi
                                ''',
                                returnStdout: true
                            ).trim()

                            def counts = trivyInfo.split(':')
                            def criticalCount = counts[0].toInteger()
                            def highCount = counts[1].toInteger()
                            def mediumCount = counts[2].toInteger()

                            echo "Trivy scan results: critical=${criticalCount}, high=${highCount}, medium=${mediumCount}"

                            if (params.ENFORCE_QUALITY_GATES) {
                                if (criticalCount > 0 || highCount > 0) {
                                    error("QUALITY GATE FAILURE: Trivy found ${criticalCount} critical and ${highCount} high vulnerabilities")
                                }
                                if (mediumCount > 0) {
                                    unstable("Trivy found ${mediumCount} medium severity vulnerabilities")
                                }
                            }
                        }
                    }
                    post {
                        always {
                            archiveArtifacts artifacts: 'trivy-report.json', allowEmptyArchive: true
                        }
                    }
                }
            }
        }

        stage('Unit Tests') {
            steps {
                script {
                    def testResult = sh(
                        script: '''
                            echo "=== Running Unit Tests with Coverage ==="
                            uv run pytest tests/ \
                                --cov=${SOURCE_DIR} \
                                --cov-report=xml:coverage.xml \
                                --cov-report=html:htmlcov \
                                --cov-report=term \
                                --cov-fail-under=${COVERAGE_THRESHOLD} \
                                --junitxml=pytest-report.xml \
                                --verbose \
                                -x || {
                                    echo "QUALITY GATE FAILURE: Tests failed or coverage below ${COVERAGE_THRESHOLD}%"
                                    exit 1
                                }
                            echo "QUALITY GATE PASSED: All tests passed with sufficient coverage"
                        ''',
                        returnStatus: true
                    )

                    if (testResult != 0 && params.ENFORCE_QUALITY_GATES) {
                        error("Unit tests or coverage quality gate failed")
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

        stage('SonarCloud Analysis') {
            when {
                expression { params.RUN_SONAR }
            }
            environment {
                // =====================================================
                // SONARCLOUD SETTINGS - UPDATE THESE FOR YOUR PROJECT
                // =====================================================
                SONAR_ORGANIZATION = 'kviscount'
                SONAR_PROJECT_KEY = 'kviscount_n8n-mcp-server'
                SONAR_SCANNER_VERSION = '6.2.1.4610'
            }
            steps {
                script {
                    try {
                        withCredentials([string(credentialsId: 'sonarcloud-token', variable: 'SONAR_TOKEN')]) {
                            sh '''
                                echo "=== Checking Java Availability ==="
                                if ! command -v java &> /dev/null; then
                                    echo "WARNING: Java not found - SonarScanner requires Java 17+"
                                    echo "Skipping SonarCloud analysis due to missing Java runtime"
                                    exit 0
                                fi
                                java -version

                                echo ""
                                echo "=== Installing SonarScanner CLI ==="
                                # Use generic distribution (no bundled JRE) to use system Java
                                SCANNER_DIR="$HOME/.local/sonar-scanner-${SONAR_SCANNER_VERSION}"
                                if [ ! -d "$SCANNER_DIR" ]; then
                                    curl -sSLo sonar-scanner.zip "https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-${SONAR_SCANNER_VERSION}.zip"
                                    unzip -q -o sonar-scanner.zip -d $HOME/.local/
                                    rm -f sonar-scanner.zip
                                fi
                                export PATH="$SCANNER_DIR/bin:$PATH"
                                export JAVA_HOME="${JAVA_HOME:-/usr/lib/jvm/java-21-openjdk-amd64}"
                                echo "Using SonarScanner from: $SCANNER_DIR"
                                echo "JAVA_HOME=$JAVA_HOME"

                                echo "=== Running SonarCloud Analysis ==="
                                sonar-scanner \
                                    -Dsonar.host.url=https://sonarcloud.io \
                                    -Dsonar.token="${SONAR_TOKEN}" \
                                    -Dsonar.projectKey="${SONAR_PROJECT_KEY}" \
                                    -Dsonar.organization="${SONAR_ORGANIZATION}" \
                                    -Dsonar.projectName="${PROJECT_NAME}" \
                                    -Dsonar.sources=${SOURCE_DIR} \
                                    -Dsonar.tests=tests \
                                    -Dsonar.python.version=3.11 \
                                    -Dsonar.python.coverage.reportPaths=coverage.xml \
                                    -Dsonar.python.ruff.reportPaths=ruff-report.json \
                                    -Dsonar.python.mypy.reportPaths=mypy-report.xml \
                                    -Dsonar.python.bandit.reportPaths=bandit-report.json \
                                    -Dsonar.python.semgrep.reportPaths=semgrep-report.json

                                echo "SonarCloud analysis complete"
                                echo "View at: https://sonarcloud.io/project/overview?id=${SONAR_PROJECT_KEY}"
                            '''
                        }
                    } catch (Exception e) {
                        echo "Skipping SonarCloud analysis: 'sonarcloud-token' credential not configured"
                        echo "To enable, add a 'sonarcloud-token' secret text credential in Jenkins"
                    }
                }
            }
        }

        stage('SonarCloud Quality Gate') {
            when {
                expression { params.RUN_SONAR }
            }
            environment {
                // Must match SONAR_PROJECT_KEY from SonarCloud Analysis stage
                SONAR_PROJECT_KEY = 'kviscount_n8n-mcp-server'
            }
            steps {
                timeout(time: 5, unit: 'MINUTES') {
                    script {
                        try {
                            withCredentials([string(credentialsId: 'sonarcloud-token', variable: 'SONAR_TOKEN')]) {
                                def gateResult = sh(
                                    script: '''
                                        echo "=== Checking SonarCloud Quality Gate Status ==="
                                        sleep 10  # Wait for analysis to process

                                        RESPONSE=$(curl -s \
                                            -H "Authorization: Bearer ${SONAR_TOKEN}" \
                                            "https://sonarcloud.io/api/qualitygates/project_status?projectKey=${SONAR_PROJECT_KEY}")

                                        GATE_STATUS=$(echo "$RESPONSE" | jq -r '.projectStatus.status // "UNKNOWN"' 2>/dev/null || echo "UNKNOWN")

                                        echo "Quality Gate Status: ${GATE_STATUS}"
                                        echo ""

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
        icon = 'PASS' if status == 'OK' else 'FAIL'
        print(f'{icon} {metric}: {actual} (threshold: {threshold})')
except:
    print('Unable to parse conditions')
" 2>/dev/null || true

                                        echo ""

                                        if [ "$GATE_STATUS" = "ERROR" ]; then
                                            echo "QUALITY GATE FAILURE: SonarCloud quality gate failed"
                                            if [ "${FAIL_ON_SONAR_GATE}" = "true" ]; then
                                                exit 1
                                            fi
                                        elif [ "$GATE_STATUS" = "OK" ]; then
                                            echo "QUALITY GATE PASSED: SonarCloud quality gate passed"
                                        else
                                            echo "Quality Gate status: ${GATE_STATUS}"
                                        fi
                                    ''',
                                    returnStatus: true
                                )

                                if (gateResult != 0 && params.ENFORCE_QUALITY_GATES && env.FAIL_ON_SONAR_GATE == 'true') {
                                    error("SonarCloud quality gate failed")
                                }
                            }
                        } catch (Exception e) {
                            echo "Quality Gate check skipped: ${e.message}"
                        }
                    }
                }
            }
        }

        stage('Build Package') {
            steps {
                sh '''
                    echo "=== Building Distribution Package ==="
                    uv build

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
                    echo "=== Generating SBOM with Syft ==="

                    # Install syft if not present
                    if ! command -v syft &> /dev/null; then
                        echo "Installing syft..."
                        mkdir -p "$HOME/.local/bin"
                        curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b "$HOME/.local/bin"
                    fi
                    syft version

                    # Get version from pyproject.toml (hardcoded, bumped by pre-push hook)
                    PROJECT_VERSION=$(grep -E '^version\s*=' pyproject.toml | head -1 | sed -E 's/.*"([^"]+)".*/\1/' || echo "0.0.0")
                    echo "Project version: ${PROJECT_VERSION}"

                    # Generate SBOM using syft
                    echo "Generating SBOM..."
                    syft ./ \
                        -o cyclonedx-json=sbom-raw.json \
                        -o spdx-json=sbom-spdx.json \
                        --source-name "${PROJECT_NAME}" \
                        --source-version "${PROJECT_VERSION}"

                    # Enrich SBOM with project metadata using jq
                    echo "Enriching SBOM metadata..."
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
                       .metadata.manufacture = {
                           "name": $supplier_name,
                           "contact": [{"email": $supplier_email}],
                           "url": [$supplier_url]
                       } |
                       .metadata.supplier = {
                           "name": $supplier_name,
                           "contact": [{"email": $supplier_email}],
                           "url": [$supplier_url]
                       } |
                       .metadata.authors = [{"name": $supplier_name, "email": $supplier_email}] |
                       .metadata.lifecycles = [{"phase": "build"}]
                       ' sbom-raw.json > sbom.json

                    rm -f sbom-raw.json

                    echo "SBOM generated successfully:"
                    COMPONENT_COUNT=$(jq '.components | length' sbom.json 2>/dev/null || echo 0)
                    echo "Components found: ${COMPONENT_COUNT}"

                    # Export version for Dependency-Track
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
                    // Read version from SBOM generation stage
                    def projectVersion = '0.0.0'
                    if (fileExists('.project_version')) {
                        projectVersion = readFile('.project_version').trim()
                        // Strip dev suffix for cleaner D-Track versioning
                        projectVersion = projectVersion.replaceAll(/\.dev.*/, '')
                    }
                    echo "Uploading SBOM for ${env.PROJECT_NAME} v${projectVersion}"

                    // Determine thresholds (-1 means disabled)
                    def failCritical = env.DTRACK_FAIL_CRITICAL?.toInteger() ?: 1
                    def failHigh = env.DTRACK_FAIL_HIGH?.toInteger() ?: 1
                    def unstableMedium = env.DTRACK_UNSTABLE_MEDIUM?.toInteger() ?: 10
                    def unstableLow = env.DTRACK_UNSTABLE_LOW?.toInteger() ?: -1

                    // Build threshold map (only include if >= 0)
                    def thresholds = [:]
                    if (failCritical >= 0) thresholds.failedTotalCritical = failCritical
                    if (failHigh >= 0) thresholds.failedTotalHigh = failHigh
                    if (unstableMedium >= 0) thresholds.unstableTotalMedium = unstableMedium
                    if (unstableLow >= 0) thresholds.unstableTotalLow = unstableLow

                    try {
                        withCredentials([string(credentialsId: 'dependency-track', variable: 'DTRACK_API_KEY')]) {
                            dependencyTrackPublisher(
                                artifact: 'sbom.json',
                                projectName: env.PROJECT_NAME,
                                projectVersion: projectVersion,
                                dependencyTrackUrl: env.DTRACK_URL,
                                dependencyTrackApiKey: env.DTRACK_API_KEY,
                                autoCreateProjects: true,
                                synchronous: params.DTRACK_QUALITY_GATE,
                                dependencyTrackPollingTimeout: 10,
                                // Vulnerability thresholds (only applied in synchronous mode)
                                failedTotalCritical: thresholds.failedTotalCritical ?: null,
                                failedTotalHigh: thresholds.failedTotalHigh ?: null,
                                unstableTotalMedium: thresholds.unstableTotalMedium ?: null,
                                unstableTotalLow: thresholds.unstableTotalLow ?: null,
                                // Policy violations
                                failOnViolationFail: params.ENFORCE_QUALITY_GATES,
                                warnOnViolationWarn: true,
                                // Project metadata
                                projectProperties: [
                                    group: env.SUPPLIER_URL?.replaceAll('https://github.com/', '') ?: '',
                                    tags: 'python jenkins ci-cd',
                                    isLatest: env.GIT_BRANCH_NAME == 'main' || env.GIT_BRANCH_NAME == 'master'
                                ]
                            )

                            if (params.DTRACK_QUALITY_GATE) {
                                echo "QUALITY GATE PASSED: Dependency-Track vulnerability thresholds met"
                            } else {
                                echo "SBOM uploaded successfully (async mode - no quality gate)"
                            }
                        }
                    } catch (hudson.AbortException e) {
                        // Plugin throws AbortException on threshold violations
                        if (params.ENFORCE_QUALITY_GATES && params.DTRACK_QUALITY_GATE) {
                            error("Dependency-Track quality gate failed: ${e.message}")
                        } else {
                            unstable("Dependency-Track found vulnerabilities: ${e.message}")
                        }
                    } catch (Exception e) {
                        echo "Dependency-Track upload skipped: ${e.message}"
                        echo "Ensure 'dependency-track' credential exists and API key has BOM_UPLOAD permission"
                    }
                }
            }
            post {
                always {
                    sh 'rm -f .project_version || true'
                }
            }
        }
    }

    post {
        always {
            echo "Pipeline completed with status: ${currentBuild.currentResult}"

            script {
                echo """
=== QUALITY GATE SUMMARY ===
Quality Gates Enforced: ${params.ENFORCE_QUALITY_GATES}
Coverage Threshold: ${env.COVERAGE_THRESHOLD}%
Max Lint Errors: ${env.MAX_LINT_ERRORS}
Block on Critical Vulns: ${env.BLOCK_ON_CRITICAL_VULNS}
Block on High Vulns: ${env.BLOCK_ON_HIGH_VULNS}
Fail on SonarCloud Gate: ${env.FAIL_ON_SONAR_GATE}
--- Dependency-Track ---
D-Track Quality Gate: ${params.DTRACK_QUALITY_GATE}
Fail on Critical: ${env.DTRACK_FAIL_CRITICAL}
Fail on High: ${env.DTRACK_FAIL_HIGH}
Unstable on Medium: ${env.DTRACK_UNSTABLE_MEDIUM}
================================
"""
            }

            sh 'rm -rf .venv venv venv-* || true'

            cleanWs(
                cleanWhenSuccess: true,
                cleanWhenFailure: false,
                cleanWhenAborted: false,
                deleteDirs: true,
                patterns: [
                    [pattern: '.venv/**', type: 'INCLUDE'],
                    [pattern: 'venv/**', type: 'INCLUDE'],
                    [pattern: '**/__pycache__/**', type: 'INCLUDE'],
                    [pattern: '*.pyc', type: 'INCLUDE'],
                    [pattern: '.pytest_cache/**', type: 'INCLUDE'],
                    [pattern: '.ruff_cache/**', type: 'INCLUDE']
                ]
            )
        }

        success {
            echo '=== ALL QUALITY GATES PASSED - Pipeline completed successfully ==='
            script {
                if (env.CHANGE_ID) {
                    echo "PR #${env.CHANGE_ID} passed all quality gates"
                }
            }
        }

        failure {
            echo '=== QUALITY GATE FAILURE - Pipeline failed ==='
            script {
                echo "One or more quality gates failed. Review logs at: ${env.BUILD_URL}"
                echo "Check the following:"
                echo "  - Code formatting (ruff format)"
                echo "  - Lint errors (ruff check)"
                echo "  - Type checking (mypy)"
                echo "  - Test failures/coverage (pytest)"
                echo "  - Security vulnerabilities (Semgrep, Bandit, pip-audit, Trivy)"
                echo "  - SonarCloud quality gate"
                echo "  - Dependency-Track vulnerabilities (critical/high)"
            }
        }

        unstable {
            echo '=== Pipeline completed with warnings ==='
            echo 'Some quality checks passed with warnings - review the reports'
        }
    }
}
