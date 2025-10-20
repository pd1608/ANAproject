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
                    # Create a virtual environment named 'venv' in the workspace
                    python3 -m venv venv
                    
                    # Activate venv and install dependencies
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
                    cd $WORKSPACE
                    . venv/bin/activate
                    python3 ping_test.py
                    '''
                }
            }
        }

        stage('Run Unit Tests') {
            steps {
                script {
                    echo "Running pytest inside the virtual environment..."
                    sh '''
                    cd $WORKSPACE
                    . venv/bin/activate
                    python3 -m pytest --junitxml=pytest_results.xml
                    '''
                }
            }
            post {
                always {
                    echo "Archiving pytest results..."
                    junit 'pytest_results.xml'
                }
            }
        }

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
            echo "✅ Ping test and unit tests completed successfully!"
        }
        failure {
            echo "❌ Build failed! Check console output for errors."
        }
    }
}
