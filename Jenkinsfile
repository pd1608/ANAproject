pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                echo "Checking out code from GitHub..."
                git branch: 'master', url: 'https://github.com/pd1608/ANAproject.git'
            }
        }

        stage('Install Dependencies') {
            steps {
                script {
                    echo "Setting up virtual environment and installing dependencies..."
                    sh '''
                        python3 -m venv /home/student/lab1/pythonscripts/venv
                        /home/student/lab1/pythonscripts/venv/bin/python3 -m pip install --upgrade pip
                        /home/student/lab1/pythonscripts/venv/bin/python3 -m pip install netmiko pytest
                    '''
                }
            }
        }

        stage('Ping Test') {
            steps {
                script {
                    echo "Running ping_test.py inside the virtual environment..."
                    sh '''
                        /home/student/lab1/pythonscripts/venv/bin/python3 /home/student/lab1/pythonscripts/ping_test.py
                    '''
                }
            }
        }

        stage('Run Unit Tests') {
            steps {
                script {
                    echo "Running pytest for safe unit tests..."
                    sh '''
                        /home/student/lab1/pythonscripts/venv/bin/python3 -m pytest /home/student/lab1/pythonscripts/tests --junitxml=/home/student/lab1/pythonscripts/pytest_results.xml --tb=short
                    '''
                }
            }
        }

        stage('Archive Test Results') {
            steps {
                echo "Archiving pytest results..."
                junit '/home/student/lab1/pythonscripts/pytest_results.xml'
            }
        }
    }

    post {
        success {
            echo "✅ Pipeline completed successfully!"
        }
        failure {
            echo "❌ Pipeline failed! Check the console output for errors."
        }
    }
}
