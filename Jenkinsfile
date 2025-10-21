pipeline {
    agent any
    stages {
        // ... (Checkout stage remains unchanged)

        stage('Install Dependencies') {
            steps {
                script {
                    echo "Setting up virtual environment and installing netmiko, pytest, and coverage..."
                    sh '''
                        # 1. Create a virtual environment named 'venv' in the workspace
                        python3 -m venv venv
                        
                        # 2. Use the explicit path to the venv's python binary to run pip as a module.
                        # This guarantees installation happens inside the new venv/lib/pythonX.Y/site-packages
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
                        # Execute pytest using the explicit python binary from the venv.
                        # Using 'cd $WORKSPACE' is redundant since the Jenkins agent starts there, but keeping it doesn't hurt.
                        cd $WORKSPACE
                        ./venv/bin/python3 -m pytest --cov=. --cov-report=xml
                    '''
                    // Optional: cobertura autoUpdate: false, coberturaReportFile: 'coverage.xml'
                }
            }
        }

        // ... (The rest of the pipeline remains unchanged)
        
        stage('Ping Test') {
            steps {
                script {
                    echo "Running ping_test.py inside the virtual environment..."
                    sh '''
                        # Execute the script using the explicit python binary from the venv
                        ./venv/bin/python3 ping_test.py
                    '''
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
