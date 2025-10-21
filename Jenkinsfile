pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                echo "Checking out code from GitHub..."
                git branch: 'master', url: 'https://github.com/pd1608/ANAproject.git'
            }
        }

        stage('Setup and Tests') {
            steps {
                script {
                    echo "Setting up venv, installing dependencies, running ping test and unit tests..."
                    sh '''
                        # Create virtual environment
                        python3 -m venv venv

                        # Activate venv and install dependencies
                        . venv/bin/activate
                        pip install --upgrade pip
                        pip install netmiko pytest

                        # Run ping test
                        python3 /home/student/lab1/pythonscripts/ping_test.py

                        # Run unit tests
                        python3 -m pytest /home/student/lab1/pythonscripts/tests \
                            --junitxml=/home/student/lab1/pythonscripts/pytest_results.xml --tb=short
                    '''
                }
            }
        }

        stage('Results') {
            steps {
                script {
                    def pingResults = '/home/student/lab1/pythonscripts/ping_results.txt'
                    def pytestResults = '/home/student/lab1/pythonscripts/pytest_results.xml'

                    echo "Displaying ping results..."
                    sh(script: "cat ${pingResults} || true", returnStatus: true)

                    echo "Archiving ping and pytest results..."
                    archiveArtifacts artifacts: "${pingResults}, ${pytestResults}", allowEmpty: true
                }
            }
        }
    }

    post {
        success {
            echo "✅ Pipeline completed successfully!"
        }
        failure {
            echo "❌ Pipeline failed! Check console output."
        }
    }
}
