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

        stage('Ping Test') {
            steps {
                script {
                    echo "Running ping_test.py directly..."
                    sh '''
                    cd $WORKSPACE
                    python3 ping_test.py > ping_results.txt
                    '''
                }
            }
        }

        stage('Results') {
            steps {
                script {
                    echo "Displaying ping results:"
                    sh 'cat $WORKSPACE/ping_results.txt'

                    // Archive results so they are downloadable from Jenkins
                    archiveArtifacts artifacts: '$WORKSPACE/ping_results.txt'
                }
            }
        }
    }

    post {
        success { echo "✅ Ping test completed successfully!" }
        failure { echo "❌ Ping test failed!" }
    }
}
