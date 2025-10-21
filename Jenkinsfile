pipeline {
    agent any
    stages {
        stage('Declarative: Checkout SCM') {
            // This stage is automatically executed by Jenkins when using Pipeline from SCM
        }
        
        stage('Checkout') {
            steps {
                echo "Checking out code from GitHub..."
                // Replicating the explicit checkout seen in the log
                git branch: 'master', url: 'https://github.com/pd1608/ANAproject.git'
            }
        }

        stage('Install Dependencies') {
            steps {
                script {
                    echo "Setting up virtual environment and installing dependencies..."
                    sh '''
                        # 1. Create a virtual environment named 'venv' in the workspace
                        python3 -m venv venv
                        
                        # 2. Activate the venv (This ensures 'pip' uses the venv's PATH)
                        # NOTE: Using 'source' requires running all commands in a single sh block or using a wrapper.
                        # Since your log shows '. venv/bin/activate' followed by 'pip', this is the successful pattern.
                        . venv/bin/activate
                        
                        # 3. Upgrade pip (as seen in log) and install dependencies
                        pip install --upgrade pip
                        pip install netmiko pytest
                        
                        # NOTE: The original log shows a complex 'deactivate' shell operation here, 
                        # which is automatically handled by Jenkins for multi-line sh blocks.
                    '''
                }
            }
        }

        stage('Ping Test') {
            steps {
                script {
                    echo "Running ping_test.py inside the virtual environment..."
                    sh '''
                        # 1. Activate the venv again for the new sh step
                        . venv/bin/activate
                        
                        # 2. Execute the script using the successful ABSOLUTE path
                        python3 /home/student/lab1/pythonscripts/ping_test.py
                    '''
                }
            }
        }
        
        stage('Run Unit Tests') {
            steps {
                script {
                    echo "Running pytest for safe unit tests..."
                    sh '''
                        # 1. Activate the venv again for the new sh step
                        . venv/bin/activate
                        
                        # 2. Execute the exact successful pytest command from the log, 
                        # using the ABSOLUTE path to the tests and XML report.
                        python3 -m pytest /home/student/lab1/pythonscripts/tests --junitxml=/home/student/lab1/pythonscripts/pytest_results.xml --tb=short
                    '''
                }
            }
        }
        
        stage('Archive Test Results') {
            when {
                // The log shows this stage skipped, but a successful pipeline would run it.
                // We'll add an explicit condition/step based on typical practice.
                expression { currentBuild.result != 'FAILURE' }
            }
            steps {
                script {
                    echo "Archiving test and ping results..."
                    // Archive the JUnit XML report
                    archiveArtifacts artifacts: '/home/student/lab1/pythonscripts/pytest_results.xml', allowEmpty: true
                    
                    // Archive the ping results
                    archiveArtifacts artifacts: '/home/student/lab1/pythonscripts/ping_results.txt', allowEmpty: true
                }
            }
        }
    }
    
    post {
        success {
            echo "✅ Pipeline succeeded! Build #33 logic replicated."
        }
        failure {
            echo "❌ Pipeline failed! Review console output. Note: Build #33 failed due to a test failure, not a setup/import issue."
        }
    }
}
