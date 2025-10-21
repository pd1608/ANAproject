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

                        # 2. Activate the virtual environment and install netmiko, pytest, and coverage
                        # We use '&&' to ensure the install only runs if activation succeeds!
                        . venv/bin/activate && pip install netmiko pytest pytest-cov
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
                        
                        # 2. Activate the virtual environment
                        . venv/bin/activate
                        
                        # 3. Execute pytest and coverage.
                        # Assuming your tests are in a 'tests' directory or follow a standard naming convention (e.g., test_*.py).
                        # --cov=. tells pytest-cov to check coverage for the current directory's code.
                        # --cov-report=xml generates a Cobertura XML report for Jenkins integration.
                        pytest --cov=. --cov-report=xml
                    '''
                    // Optional: Publish the Cobertura coverage report if you have the Cobertura plugin installed in Jenkins
                    // This allows Jenkins to track coverage trends.
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
                        
                        # 2. Activate the virtual environment using the universal '.' command
                        . venv/bin/activate
                        
                        # 3. Execute the script using the python binary from the venv
                        python3 ping_test.py
                    '''
                }
            }
        }

        stage('Results') {
            when {
                // Only run this stage if the previous stages (including tests) were successful
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
