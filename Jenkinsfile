pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                echo "Checking out code from GitHub..."
                git branch: 'master', url: 'https://github.com/pd1608/ANAproject.git'
            }
        }

        stage('Setup Virtual Environment') {
            steps {
                echo "Setting up Python virtual environment and installing dependencies..."
                sh '''
                    python3 -m venv venv
                    source venv/bin/activate
                    pip install --upgrade pip
                    pip install netmiko pytest
                '''
            }
        }

        stage('Ping Test') {
            steps {
                echo "Running ping_test.py inside virtual environment..."
                sh '''
                    source venv/bin/activate
                    python3 /home/student/lab1/pythonscripts/ping_test.py
                '''
            }
        }

        stage('Unit Tests') {
            steps {
                echo "Running pytest for unit tests..."
                sh '''
                    source venv/bin/activate
                    python3 -m pytest /home/student/lab1/pythonscripts/tests \
                        --junitxml=/home/student/lab1/pythonscripts/pytest_results.xml --tb=short
                '''
            }
        }

        stage('Results') {
            steps {
                echo "Archiving test results..."
                archiveArtifacts artifacts: '/home/student/lab1/pythonscripts/ping_results.txt, /home/student/lab1/pythonscripts/pytest_results.xml', allowEmpty: true
            }
        }
    }

    post {
        success {
            echo "✅ Pipeline succeeded!"
        }
        failure {
            echo "❌ Pipeline failed! Check console output."
        }
    }
}
