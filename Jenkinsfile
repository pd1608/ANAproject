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
                        
                        # 2. Activate the virtual environment and install dependencies
                        # Note: We must install 'pytest-cov' for coverage reporting.
                        . venv/bin/activate
                        pip install --upgrade pip
                        pip install netmiko pytest pytest-cov
                    '''
                }
            }
        }
        
        // --- NEW STAGE FOR UNIT TESTS AND COVERAGE ---
        stage('Run Unit Tests') {
            steps {
                script {
                    echo "Running pytest for safe unit tests..."
                    sh '''
                        # Activate the venv for test execution
                        . venv/bin/activate
                        
                        # Use the ABSOLUTE paths from the successful log to ensure 'pythonscripts' is found.
                        # The coverage part will need to be explicitly added here since it wasn't in the successful log's command.
                        # We'll use the command you requested previously, ensuring it runs from the venv environment.
                        # The key is running 'pytest' from the venv *after* activation.
                        
                        pytest -v --cov=pythonscripts --cov-report=term-missing
                        
                        # If the above fails to find 'pythonscripts', revert to the ABSOLUTE path that worked previously:
                        # python3 -m pytest /home/student/lab1/pythonscripts/tests --junitxml=/home/student/lab1/pythonscripts/pytest_results.xml --tb=short
                    '''
                }
            }
        }
        // ---------------------------------------------

        stage('Ping Test') {
            steps {
                script {
                    echo "Running ping_test.py inside the virtual environment..."
                    sh '''
                        # 1. Activate the virtual environment
                        . venv/bin/activate
                        
                        # 2. Execute the script using the successful ABSOLUTE path from the log
                        python3 /home/student/lab1/pythonscripts/ping_test.py
                    '''
                }
            }
        }

        stage('Results') {
            when {
                // Run if the build was successful, or if it failed *only* during the tests (which is expected).
                expression { currentBuild.result != 'NOT_BUILT' }
            }
            steps {
                script {
                    // NOTE: The Python script hardcodes the log file path.
                    def resultFilePath = '/home/student/lab1/pythonscripts/ping_results.txt'
                    def testResultPath = '/home/student/lab1/pythonscripts/pytest_results.xml'
                    
                    echo "Archiving results..."
                    
                    // Archive the JUnit XML report (for test failure info)
                    archiveArtifacts artifacts: testResultPath, allowEmpty: true
                    
                    // Display and archive the ping results
                    echo "Displaying ping results (if file exists at expected path)..."
                    sh(script: "cat ${resultFilePath} || true", returnStatus: true)
                    archiveArtifacts artifacts: resultFilePath, allowEmpty: true
                }
            }
        }
    }
    
    post {
        success {
            echo "✅ Pipeline succeeded! Ping test completed successfully!"
        }
        failure {
            echo "❌ Pipeline failed! Review the console output for errors. (Note: A test failure is expected based on the log, but environment setup should pass)."
        }
    }
}
