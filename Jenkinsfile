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
                        # 1. Create a virtual environment named 'venv' in the workspace
                        python3 -m venv venv
                        # 2. Activate the virtual environment and install required packages
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
                        # 1. Change to the workspace root
                        cd $WORKSPACE
                        # 2. Activate the virtual environment
                        . venv/bin/activate
                        # 3. Execute the ping test script
                        python3 ping_test.py
                    '''
                }
            }
        }

        stage('Unit Tests') {
            steps {
                script {
                    echo "Running pytest for unit tests..."
                    sh '''
                        # Activate virtual environment
                        . venv/bin/activate
                        # Run pytest and generate junit XML results
                        python3 -m pytest /home/student/lab1/pythonscripts/tests --junitxml=/home/student/lab1/pythonscripts/pytest_results.xml --tb=short
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
                    // Display ping results
                    def pingResultFile = '/home/student/lab1/pythonscripts/ping_results.txt'
                    echo "Displaying ping results (if file exists)..."
                    sh(script: "cat ${pingResultFile} || true", returnStatus: true)

                    // Archive ping and pytest results
                    archiveArtifacts artifacts: pingResultFile, allowEmpty: true
                    archiveArtifacts artifacts: '/home/student/lab1/pythonscripts/pytest_results.xml', allowEmpty: true

                    // Publish junit results for Jenkins test reporting
                    junit '/home/student/lab1/pythonscripts/pytest_results.xml'
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
