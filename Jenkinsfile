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
                    # Create a virtual environment named 'venv'
                    python3 -m venv venv
                    # Activate the virtual environment and install dependencies
                    . venv/bin/activate
                    pip install --upgrade pip
                    pip install netmiko pytest pytest-cov
                    '''
                }
            }
        }

        stage('Ping Test') {
            steps {
                script {
                    echo "Running ping_test.py inside the virtual environment..."
                    sh '''
                    cd $WORKSPACE
                    . venv/bin/activate
                    python3 ping_test.py
                    '''
                }
            }
        }

        stage('Unit Tests') {
            steps {
                sh '''
                    . venv/bin/activate
                    # Set Python path to repo root so pytest can find 'pythonscripts'
                    export PYTHONPATH=$PWD
                    pytest -v --rootdir=$PWD --cov=pythonscripts --cov-report=term-missing tests/
                '''
            }
        }
    }


        stage('Results') {
            when {
                expression { currentBuild.result == null || currentBuild.result == 'SUCCESS' }
            }
            steps {
                script {
                    def pingResults = "$WORKSPACE/pythonscripts/ping_results.txt"
                    echo "Displaying ping results (if file exists)..."
                    sh(script: "cat ${pingResults} || true", returnStatus: true)
                    archiveArtifacts artifacts: pingResults, allowEmptyArchive: true
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
