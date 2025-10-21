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
                    echo "Setting up virtual environment and installing netmiko..."
                    sh '''
                    # 1. Create a virtual environment named 'venv' in the workspace
                    python3 -m venv venv
                    # 2. Activate the virtual environment and install netmiko
                    . venv/bin/activate && pip install netmiko
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
                    # 2. Activate the virtual environment
                    . venv/bin/activate
                    # 3. Run the ping test script
                    python3 ping_test.py
                    '''
                }
            }
        }

        stage('Unit Tests') {
            steps {
                script {
                    echo "Running pytest with coverage..."
                    sh '''
                    # Run pytest with coverage exactly like your local command
                    cd /home/student/lab1
                    pytest -v --cov=pythonscripts --cov-report=term-missing
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
                    // NOTE: The Python script hardcodes the log file path
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
            echo "✅ Pipeline completed successfully!"
        }
        failure {
            echo "❌ Pipeline failed! Review the console output for errors."
        }
    }
}
