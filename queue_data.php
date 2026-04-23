<?php
session_start();
header('Content-Type: application/json');

$host = 'localhost';
$user = 'root';
$password = '';
$database = 'app';

$conn = new mysqli($host, $user, $password, $database);
if ($conn->connect_error) {
    echo json_encode(['error' => 'Database connection failed']);
    exit;
}

$prep = $conn->query("SELECT order_code, created_at FROM orders WHERE status = 'waiting' ORDER BY created_at ASC LIMIT 30");
$preparing = [];
while ($row = $prep->fetch_assoc()) {
    $preparing[] = [
        'code' => $row['order_code'],
        'status' => 'waiting',
        'time' => date('g:i A', strtotime($row['created_at']))
    ];
}

$serv = $conn->query("SELECT order_code, created_at FROM orders WHERE status = 'serving' ORDER BY created_at ASC LIMIT 10");
$serving = [];
while ($row = $serv->fetch_assoc()) {
    $serving[] = [
        'code' => $row['order_code'],
        'time' => date('g:i A', strtotime($row['created_at']))
    ];
}

echo json_encode(['preparing' => $preparing, 'serving' => $serving]);
?>