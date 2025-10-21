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
                        python3 -m venv venv
                        # Upgrade pip and install required packages
                        /var/lib/jenkins/workspace/Containerlab/venv/bin/pip install --upgrade pip
                        /var/lib/jenkins/workspace/Containerlab/venv/bin/pip install netmiko pytest
                    '''
                }
            }
        }

        stage('Ping Test') {
            steps {
                script {
                    echo "Running ping_test.py inside the virtual environment..."
                    sh '''
                        /var/lib/jenkins/workspace/Containerlab/venv/bin/python3 /home/student/lab1/pythonscripts/ping_test.py
                    '''
                }
            }
        }

        stage('Unit Tests') {
            steps {
                script {
                    echo "Running pytest for unit tests..."
                    sh '''
                        /var/lib/jenkins/workspace/Containerlab/venv/bin/python3 -m pytest \
                        /home/student/lab1/pythonscripts/tests \
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

                    echo "Displaying ping results (if file exists)..."
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
            echo "❌ Pipeline failed! Review the console output for errors."
        }
    }
}
