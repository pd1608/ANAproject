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

                        # 2. Use the explicit path to the venv's pip to ensure installation
                        # happens correctly inside the new venv/lib/pythonX.Y/site-packages
                        ./venv/bin/pip install netmiko pytest pytest-cov
                    '''
                }
            }
        }

        stage('Unit Tests & Coverage') {
            steps {
                script {
                    echo "Running unit tests with pytest and generating coverage report..."
                    sh '''
                        # 1. Change to the workspace root
                        cd $WORKSPACE
                        
                        # 2. Execute pytest using the explicit python binary from the venv.
                        # This guarantees the venv is used, and it should now find 'pytest' 
                        # because it was installed correctly with the explicit pip path above.
                        ./venv/bin/python3 -m pytest --cov=. --cov-report=xml
                    '''
                    // Optional: You can still uncomment the below if the Cobertura plugin is installed
                    // cobertura autoUpdate: false, coberturaReportFile: 'coverage.xml'
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
        
        // ... (The rest of the pipeline remains the same)
        stage('Results') {
            when {
                expression { currentBuild.result == 'SUCCESS' }
            }
            steps {
                script {
                    def resultFilePath = '/home/student/lab1/pythonscripts/ping_results.txt'
                    echo "Displaying ping results (if file exists at expected path)..."
                    sh(script: "cat ${resultFilePath} || true", returnStatus: true)
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
