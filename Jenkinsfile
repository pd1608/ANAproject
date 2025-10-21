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
                    echo "Setting up virtual environment and installing netmiko, pytest, and coverage..."
                    sh '''
                        # 1. Create a virtual environment named 'venv' in the workspace
                        python3 -m venv venv
                        
                        # 2. Use the explicit path to the venv's python binary to run pip as a module.
                        ./venv/bin/python3 -m pip install netmiko pytest pytest-cov
                    '''
                }
            }
        }

        stage('Unit Tests & Coverage') {
            steps {
                script {
                    echo "Running unit tests with pytest and generating coverage report..."
                    sh '''
                        # 1. Add the current workspace directory to the Python path 
                        # to enable 'from pythonscripts import...' imports.
                        export PYTHONPATH=$PYTHONPATH:$WORKSPACE
                        
                        # 2. Execute the user's preferred pytest command using the explicit venv Python interpreter.
                        ./venv/bin/python3 -m pytest -v --cov=pythonscripts --cov-report=term-missing
                    '''
                }
            }
        }

        stage('Ping Test') {
            steps {
                script {
                    echo "Running ping_test.py inside the virtual environment..."
                    sh '''
                        # 1. Change to the workspace root
                        cd $WORKSPACE
                        
                        # 2. Execute the script using the explicit python binary from the venv
                        ./venv/bin/python3 ping_test.py
                    '''
                }
            }
        }
        
        stage('Results') {
            when {
                expression { currentBuild.result == 'SUCCESS' }
            }
            steps {
                script {
                    // NOTE: The Python script hardcodes the log file path.
                    def resultFilePath = '/home/student/lab1/pythonscripts/ping_results.txt'
                    echo "Displaying ping results (if file exists at expected path)..."
                    // Use '|| true' to prevent the pipeline from failing if the file doesn't exist yet
                    sh(script: "cat ${resultFilePath} || true", returnStatus: true)
                    // Archive the results
                    archiveArtifacts artifacts: resultFilePath, allowEmpty: true
                }
            }
        }
    }
    
    post {
        success {
            echo "✅ Build, tests, and ping test completed successfully!"
        }
        failure {
            echo "❌ Pipeline failed! Review the console output for errors."
        }
    }
}
