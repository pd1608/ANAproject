pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                echo "Checking out code from GitHub..."
                git branch: 'master',
                    url: 'https://github.com/pd1608/ANAproject.git'
            }
        }

        stage('Install Dependencies') {
            steps {
                script {
                    echo "Setting up virtual environment and installing dependencies..."
                    sh '''
                    python3 -m venv venv
                    . venv/bin/activate && pip install --upgrade pip
                    . venv/bin/activate && pip install netmiko pytest
                    '''
                }
            }
        }

        stage('Ping Test') {
            steps {
                script {
                    echo "Running ping_test.py inside the virtual environment..."
                    sh '''
                    . venv/bin/activate
                    python3 ping_test.py
                    '''
                }
            }
        }

        stage('Run Unit Tests') {
            steps {
                script {
                    echo "Running pytest for safe unit tests..."
                    sh '''
                    . venv/bin/activate
                    # Run only tests in 'tests/' directory (mocked tests)
                    python3 -m pytest pythonscripts/tests --junitxml=pytest_results.xml --tb=short
                    '''
                }
            }
        }

        stage('Archive Test Results') {
            steps {
                echo "Archiving pytest results..."
                junit 'pytest_results.xml'
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
