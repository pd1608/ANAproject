pipeline {
    agent any

    environment {
        VENV_PATH = "venv"
        PYTHON_SCRIPT_DIR = "/home/student/lab1/pythonscripts"
    }

    stages {
        stage('Checkout from GitHub') {
            steps {
                echo "Checking out code from GitHub..."
                checkout scm
            }
        }

        stage('Setup Python Environment') {
            steps {
                echo "Setting up Python virtual environment..."
                sh '''
                python3 -m venv ${VENV_PATH}
                . ${VENV_PATH}/bin/activate
                pip install --upgrade pip
                pip install -r ${PYTHON_SCRIPT_DIR}/requirements.txt
                '''
            }
        }

        stage('Code Quality Check (PEP8)') {
            steps {
                echo "Running pylint for PEP8 compliance..."
                sh '''
                . ${VENV_PATH}/bin/activate
                pylint ${PYTHON_SCRIPT_DIR} --exit-zero > pylint_report.txt
                '''
            }
        }

        stage('Run Unit Tests with Coverage') {
            steps {
                script {
                    echo "Running pytest with coverage reporting..."
                    sh '''
                    . venv/bin/activate
                    pytest \
                        /home/student/lab1/pythonscripts/tests \
                        --cov=/home/student/lab1/pythonscripts \
                        --cov-report=term-missing \
                        --junitxml=/home/student/lab1/pythonscripts/pytest_results.xml \
                        --tb=short
                    '''
                }
            }
        }

        stage('Archive Results') {
            steps {
                echo "Archiving test and lint reports..."
                archiveArtifacts artifacts: 'pylint_report.txt, /home/student/lab1/pythonscripts/pytest_results.xml', onlyIfSuccessful: true
                junit '/home/student/lab1/pythonscripts/pytest_results.xml'
            }
        }
    }

    post {
        always {
            echo "Cleaning up workspace..."
            cleanWs()
        }
        success {
            echo "Build completed successfully!"
        }
        failure {
            echo "Build failed! Please check test and lint reports for details."
        }
    }
}
