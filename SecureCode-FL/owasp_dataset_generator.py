"""
OWASP Top 10 API Vulnerability Dataset Generator
=================================================

Generates 1000 synthetic code samples (500 vulnerable, 500 secure)
focusing on OWASP Top 10 API Security Risks (2023).

Each category gets 50 vulnerable + 50 secure samples.
"""

import random
import csv
import os
from datetime import datetime

# Random seeds for reproducibility
random.seed(42)

# Variable name pools
USER_VARS = ['user', 'current_user', 'auth_user', 'logged_user', 'req_user']
ID_VARS = ['id', 'user_id', 'account_id', 'resource_id', 'item_id', 'obj_id']
TOKEN_VARS = ['token', 'auth_token', 'access_token', 'jwt_token', 'bearer_token']
DATA_VARS = ['data', 'payload', 'body', 'content', 'request_data']
URL_VARS = ['url', 'target_url', 'endpoint', 'api_url', 'service_url']

# Decorator variations
AUTH_DECORATORS = ['@login_required', '@jwt_required', '@auth_required', '@token_required']
ROLE_DECORATORS = ['@admin_required', '@role_required("admin")', '@require_role("admin")', '@check_permission("admin")']

def random_func_name(prefix):
    """Generate random function name."""
    suffixes = ['_handler', '_endpoint', '_api', '_view', '_route', '']
    return f"{prefix}{random.choice(suffixes)}"


# =============================================================================
# OWASP API 1: Broken Object Level Authorization (BOLA)
# =============================================================================

def gen_bola_vulnerable():
    """Generate BOLA vulnerable samples - missing ownership check."""
    templates = [
        # Direct ID access without ownership check
        '''@app.route('/api/user/<{id_var}>')
def {func_name}({id_var}):
    {data_var} = db.query(User).filter_by(id={id_var}).first()
    return jsonify({data_var}.to_dict())''',
        
        # Order access without user verification
        '''@app.route('/api/orders/<order_id>')
def {func_name}(order_id):
    order = Order.query.get(order_id)
    if not order:
        abort(404)
    return jsonify(order.serialize())''',
        
        # Document download without authorization
        '''@app.route('/documents/<doc_id>/download')
def {func_name}(doc_id):
    doc = Document.query.get_or_404(doc_id)
    return send_file(doc.filepath)''',
        
        # Profile update without ownership verification
        '''@app.route('/api/profile/<profile_id>', methods=['PUT'])
def {func_name}(profile_id):
    {data_var} = request.get_json()
    profile = Profile.query.get(profile_id)
    profile.update({data_var})
    db.session.commit()
    return jsonify(success=True)''',
        
        # Transaction access without user check
        '''@app.route('/transactions/<txn_id>')
def {func_name}(txn_id):
    txn = Transaction.query.filter_by(id=txn_id).first()
    return jsonify(amount=txn.amount, status=txn.status)'''
    ]
    
    samples = []
    for _ in range(50):
        template = random.choice(templates)
        code = template.format(
            id_var=random.choice(ID_VARS),
            func_name=random_func_name('get_resource'),
            data_var=random.choice(DATA_VARS),
            user_var=random.choice(USER_VARS)
        )
        samples.append(('Error', code, 'BOLA'))
    return samples


def gen_bola_secure():
    """Generate BOLA secure samples - proper ownership check."""
    templates = [
        # Ownership verification before access
        '''@app.route('/api/user/<{id_var}>')
@login_required
def {func_name}({id_var}):
    if str(current_user.id) != str({id_var}):
        abort(403)
    {data_var} = db.query(User).filter_by(id={id_var}).first()
    return jsonify({data_var}.to_dict())''',
        
        # Order access with user verification
        '''@app.route('/api/orders/<order_id>')
@jwt_required
def {func_name}(order_id):
    order = Order.query.get(order_id)
    if not order or order.user_id != current_user.id:
        abort(403)
    return jsonify(order.serialize())''',
        
        # Document download with authorization
        '''@app.route('/documents/<doc_id>/download')
@login_required
def {func_name}(doc_id):
    doc = Document.query.get_or_404(doc_id)
    if doc.owner_id != current_user.id:
        abort(403)
    return send_file(doc.filepath)''',
        
        # Profile update with ownership check
        '''@app.route('/api/profile/<profile_id>', methods=['PUT'])
@auth_required
def {func_name}(profile_id):
    if profile_id != current_user.profile_id:
        return jsonify(error='Unauthorized'), 403
    {data_var} = request.get_json()
    profile = Profile.query.get(profile_id)
    profile.update({data_var})
    db.session.commit()
    return jsonify(success=True)''',
        
        # Transaction with user filter
        '''@app.route('/transactions/<txn_id>')
@login_required
def {func_name}(txn_id):
    txn = Transaction.query.filter_by(id=txn_id, user_id=current_user.id).first()
    if not txn:
        abort(404)
    return jsonify(amount=txn.amount, status=txn.status)'''
    ]
    
    samples = []
    for _ in range(50):
        template = random.choice(templates)
        code = template.format(
            id_var=random.choice(ID_VARS),
            func_name=random_func_name('get_resource'),
            data_var=random.choice(DATA_VARS)
        )
        samples.append(('Good', code, 'BOLA'))
    return samples


# =============================================================================
# OWASP API 2: Broken Authentication
# =============================================================================

def gen_broken_auth_vulnerable():
    """Generate Broken Authentication vulnerable samples."""
    templates = [
        # No token validation
        '''@app.route('/api/data')
def {func_name}():
    {token_var} = request.headers.get('Authorization')
    # No validation of token
    return jsonify(get_sensitive_data())''',
        
        # Weak password comparison
        '''@app.route('/login', methods=['POST'])
def {func_name}():
    username = request.form['username']
    password = request.form['password']
    user = User.query.filter_by(username=username).first()
    if user.password == password:  # Plain text comparison!
        return jsonify(token=generate_token(user))
    return jsonify(error='Invalid'), 401''',
        
        # Hardcoded credentials
        '''@app.route('/admin/login', methods=['POST'])
def {func_name}():
    if request.form['password'] == 'admin123':
        session['admin'] = True
        return redirect('/dashboard')
    return 'Access denied', 401''',
        
        # JWT without signature verification
        '''@app.route('/api/protected')
def {func_name}():
    {token_var} = request.headers.get('Authorization', '').replace('Bearer ', '')
    payload = jwt.decode({token_var}, options={{"verify_signature": False}})
    return jsonify(data=payload)''',
        
        # No session expiry
        '''@app.route('/api/user')
def {func_name}():
    session_id = request.cookies.get('session')
    user = sessions.get(session_id)  # No expiry check
    if user:
        return jsonify(user)
    return jsonify(error='Not found'), 404'''
    ]
    
    samples = []
    for _ in range(50):
        template = random.choice(templates)
        code = template.format(
            token_var=random.choice(TOKEN_VARS),
            func_name=random_func_name('authenticate')
        )
        samples.append(('Error', code, 'BrokenAuth'))
    return samples


def gen_broken_auth_secure():
    """Generate Broken Authentication secure samples."""
    templates = [
        # Proper token validation
        '''@app.route('/api/data')
@jwt_required()
def {func_name}():
    current_user = get_jwt_identity()
    if not current_user:
        abort(401)
    return jsonify(get_user_data(current_user))''',
        
        # Secure password hashing
        '''@app.route('/login', methods=['POST'])
def {func_name}():
    username = request.form['username']
    password = request.form['password']
    user = User.query.filter_by(username=username).first()
    if user and bcrypt.check_password_hash(user.password_hash, password):
        {token_var} = create_access_token(identity=user.id, expires_delta=timedelta(hours=1))
        return jsonify(token={token_var})
    return jsonify(error='Invalid credentials'), 401''',
        
        # Multi-factor authentication
        '''@app.route('/admin/login', methods=['POST'])
@limiter.limit("5 per minute")
def {func_name}():
    user = authenticate_user(request.form['username'], request.form['password'])
    if user and verify_mfa(user, request.form['otp']):
        session['admin'] = True
        session.permanent = True
        return redirect('/dashboard')
    return 'Access denied', 401''',
        
        # JWT with proper verification
        '''@app.route('/api/protected')
def {func_name}():
    {token_var} = request.headers.get('Authorization', '').replace('Bearer ', '')
    try:
        payload = jwt.decode({token_var}, SECRET_KEY, algorithms=['HS256'])
        if is_token_revoked(payload['jti']):
            abort(401)
        return jsonify(data=payload)
    except jwt.ExpiredSignatureError:
        abort(401)''',
        
        # Session with expiry
        '''@app.route('/api/user')
def {func_name}():
    session_id = request.cookies.get('session')
    session_data = sessions.get(session_id)
    if session_data and session_data['expires_at'] > datetime.utcnow():
        return jsonify(session_data['user'])
    return jsonify(error='Session expired'), 401'''
    ]
    
    samples = []
    for _ in range(50):
        template = random.choice(templates)
        code = template.format(
            token_var=random.choice(TOKEN_VARS),
            func_name=random_func_name('authenticate')
        )
        samples.append(('Good', code, 'BrokenAuth'))
    return samples


# =============================================================================
# OWASP API 3: Broken Object Property Level Authorization
# =============================================================================

def gen_mass_assignment_vulnerable():
    """Generate Mass Assignment vulnerable samples."""
    templates = [
        # Direct update from request
        '''@app.route('/api/user/update', methods=['PUT'])
def {func_name}():
    user = current_user
    {data_var} = request.get_json()
    for key, value in {data_var}.items():
        setattr(user, key, value)  # Mass assignment vulnerability!
    db.session.commit()
    return jsonify(success=True)''',
        
        # No field filtering
        '''@app.route('/api/profile', methods=['PATCH'])
def {func_name}():
    profile = Profile.query.get(current_user.profile_id)
    profile.update(**request.json)  # All fields updated!
    db.session.commit()
    return jsonify(profile.to_dict())''',
        
        # Admin field exposure
        '''@app.route('/api/register', methods=['POST'])
def {func_name}():
    {data_var} = request.get_json()
    user = User(**{data_var})  # User can set is_admin=True!
    db.session.add(user)
    db.session.commit()
    return jsonify(id=user.id)''',
        
        # Bulk update without filtering
        '''@app.route('/api/settings', methods=['PUT'])
def {func_name}():
    settings = Settings.query.filter_by(user_id=current_user.id).first()
    for k, v in request.form.items():
        if hasattr(settings, k):
            setattr(settings, k, v)
    db.session.commit()
    return jsonify(settings.serialize())''',
        
        # Model.update vulnerability
        '''@app.route('/account/edit', methods=['POST'])
def {func_name}():
    Account.query.filter_by(id=current_user.account_id).update(request.json)
    db.session.commit()
    return redirect('/account')'''
    ]
    
    samples = []
    for _ in range(50):
        template = random.choice(templates)
        code = template.format(
            data_var=random.choice(DATA_VARS),
            func_name=random_func_name('update_user')
        )
        samples.append(('Error', code, 'MassAssignment'))
    return samples


def gen_mass_assignment_secure():
    """Generate Mass Assignment secure samples."""
    templates = [
        # Whitelist allowed fields
        '''@app.route('/api/user/update', methods=['PUT'])
@login_required
def {func_name}():
    allowed_fields = ['name', 'email', 'phone']
    {data_var} = request.get_json()
    user = current_user
    for key in allowed_fields:
        if key in {data_var}:
            setattr(user, key, {data_var}[key])
    db.session.commit()
    return jsonify(success=True)''',
        
        # Schema validation
        '''@app.route('/api/profile', methods=['PATCH'])
@login_required
def {func_name}():
    schema = ProfileUpdateSchema()
    {data_var} = schema.load(request.json)  # Only allowed fields
    profile = Profile.query.get(current_user.profile_id)
    profile.name = {data_var}.get('name', profile.name)
    profile.bio = {data_var}.get('bio', profile.bio)
    db.session.commit()
    return jsonify(profile.to_dict())''',
        
        # Explicit field assignment
        '''@app.route('/api/register', methods=['POST'])
def {func_name}():
    {data_var} = request.get_json()
    user = User(
        username={data_var}.get('username'),
        email={data_var}.get('email'),
        password_hash=hash_password({data_var}.get('password')),
        is_admin=False  # Always false for new users
    )
    db.session.add(user)
    db.session.commit()
    return jsonify(id=user.id)''',
        
        # DTO pattern
        '''@app.route('/api/settings', methods=['PUT'])
@auth_required
def {func_name}():
    dto = SettingsDTO.from_request(request.form)
    settings = Settings.query.filter_by(user_id=current_user.id).first()
    settings.theme = dto.theme
    settings.notifications = dto.notifications
    # is_premium and role are not updateable
    db.session.commit()
    return jsonify(settings.serialize())''',
        
        # Marshmallow schema
        '''@app.route('/account/edit', methods=['POST'])
@login_required
def {func_name}():
    schema = AccountUpdateSchema(only=['name', 'timezone', 'language'])
    validated = schema.load(request.json)
    current_user.account.update(**validated)
    db.session.commit()
    return redirect('/account')'''
    ]
    
    samples = []
    for _ in range(50):
        template = random.choice(templates)
        code = template.format(
            data_var=random.choice(DATA_VARS),
            func_name=random_func_name('update_user')
        )
        samples.append(('Good', code, 'MassAssignment'))
    return samples


# =============================================================================
# OWASP API 4: Unrestricted Resource Consumption
# =============================================================================

def gen_no_rate_limit_vulnerable():
    """Generate No Rate Limiting vulnerable samples."""
    templates = [
        # No rate limit on login
        '''@app.route('/login', methods=['POST'])
def {func_name}():
    # No rate limiting - allows brute force!
    username = request.form['username']
    password = request.form['password']
    if authenticate(username, password):
        return jsonify(token=create_token(username))
    return jsonify(error='Invalid'), 401''',
        
        # Unlimited API calls
        '''@app.route('/api/search')
def {func_name}():
    query = request.args.get('q')
    # No limit on results or requests
    results = db.query(Item).filter(Item.name.contains(query)).all()
    return jsonify([r.to_dict() for r in results])''',
        
        # No file size limit
        '''@app.route('/upload', methods=['POST'])
def {func_name}():
    file = request.files['file']
    # No size check - DoS vulnerability!
    file.save(os.path.join(UPLOAD_DIR, file.filename))
    return jsonify(success=True)''',
        
        # No pagination
        '''@app.route('/api/users')
def {func_name}():
    users = User.query.all()  # Returns ALL users - memory exhaustion
    return jsonify([u.serialize() for u in users])''',
        
        # Unlimited export
        '''@app.route('/export/all')
def {func_name}():
    records = Record.query.all()  # Millions of rows possible
    return Response(
        generate_csv(records),
        mimetype='text/csv'
    )'''
    ]
    
    samples = []
    for _ in range(50):
        template = random.choice(templates)
        code = template.format(func_name=random_func_name('handle_request'))
        samples.append(('Error', code, 'NoRateLimit'))
    return samples


def gen_rate_limit_secure():
    """Generate Rate Limiting secure samples."""
    templates = [
        # Rate limited login
        '''@app.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
def {func_name}():
    username = request.form['username']
    password = request.form['password']
    if authenticate(username, password):
        return jsonify(token=create_token(username))
    return jsonify(error='Invalid'), 401''',
        
        # Paginated search with limit
        '''@app.route('/api/search')
@limiter.limit("100 per hour")
def {func_name}():
    query = request.args.get('q')
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('limit', 20, type=int), 100)
    results = db.query(Item).filter(Item.name.contains(query)).paginate(page, per_page)
    return jsonify(items=[r.to_dict() for r in results.items], total=results.total)''',
        
        # File size validation
        '''@app.route('/upload', methods=['POST'])
@limiter.limit("10 per hour")
def {func_name}():
    file = request.files['file']
    if file.content_length > MAX_FILE_SIZE:
        abort(413)
    if not allowed_file(file.filename):
        abort(400)
    filename = secure_filename(file.filename)
    file.save(os.path.join(UPLOAD_DIR, filename))
    return jsonify(success=True)''',
        
        # Paginated users
        '''@app.route('/api/users')
@login_required
@limiter.limit("30 per minute")
def {func_name}():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 50)
    users = User.query.paginate(page=page, per_page=per_page)
    return jsonify(users=[u.serialize() for u in users.items], total=users.total)''',
        
        # Chunked export with limit
        '''@app.route('/export/all')
@admin_required
@limiter.limit("1 per hour")
def {func_name}():
    limit = min(request.args.get('limit', 10000, type=int), 10000)
    records = Record.query.limit(limit).all()
    return Response(
        generate_csv(records),
        mimetype='text/csv'
    )'''
    ]
    
    samples = []
    for _ in range(50):
        template = random.choice(templates)
        code = template.format(func_name=random_func_name('handle_request'))
        samples.append(('Good', code, 'NoRateLimit'))
    return samples


# =============================================================================
# OWASP API 5: Broken Function Level Authorization
# =============================================================================

def gen_broken_func_auth_vulnerable():
    """Generate Broken Function Level Authorization vulnerable samples."""
    templates = [
        # No admin check
        '''@app.route('/admin/users')
def {func_name}():
    users = User.query.all()
    return jsonify([u.to_dict() for u in users])''',
        
        # Delete without permission
        '''@app.route('/api/post/<post_id>', methods=['DELETE'])
def {func_name}(post_id):
    post = Post.query.get(post_id)
    db.session.delete(post)
    db.session.commit()
    return jsonify(deleted=True)''',
        
        # Config access without role check
        '''@app.route('/api/config', methods=['PUT'])
def {func_name}():
    config = request.get_json()
    update_system_config(config)  # Any user can modify!
    return jsonify(success=True)''',
        
        # User promotion without auth
        '''@app.route('/api/user/<{id_var}>/promote', methods=['POST'])
def {func_name}({id_var}):
    user = User.query.get({id_var})
    user.role = 'admin'
    db.session.commit()
    return jsonify(success=True)''',
        
        # Financial action without role
        '''@app.route('/api/refund', methods=['POST'])
def {func_name}():
    order_id = request.json['order_id']
    amount = request.json['amount']
    process_refund(order_id, amount)  # No role verification!
    return jsonify(refunded=True)'''
    ]
    
    samples = []
    for _ in range(50):
        template = random.choice(templates)
        code = template.format(
            id_var=random.choice(ID_VARS),
            func_name=random_func_name('admin_action')
        )
        samples.append(('Error', code, 'BrokenFuncAuth'))
    return samples


def gen_func_auth_secure():
    """Generate Function Level Authorization secure samples."""
    templates = [
        # Admin decorator
        '''@app.route('/admin/users')
@admin_required
def {func_name}():
    users = User.query.all()
    return jsonify([u.to_dict() for u in users])''',
        
        # Permission-based delete
        '''@app.route('/api/post/<post_id>', methods=['DELETE'])
@login_required
def {func_name}(post_id):
    post = Post.query.get(post_id)
    if post.author_id != current_user.id and not current_user.is_admin:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    return jsonify(deleted=True)''',
        
        # Role-based config access
        '''@app.route('/api/config', methods=['PUT'])
@require_role('superadmin')
def {func_name}():
    config = request.get_json()
    audit_log('config_update', current_user.id, config)
    update_system_config(config)
    return jsonify(success=True)''',
        
        # User promotion with auth
        '''@app.route('/api/user/<{id_var}>/promote', methods=['POST'])
@admin_required
def {func_name}({id_var}):
    if not current_user.has_permission('manage_users'):
        abort(403)
    user = User.query.get({id_var})
    user.role = 'admin'
    audit_log('user_promoted', current_user.id, {id_var})
    db.session.commit()
    return jsonify(success=True)''',
        
        # Financial action with role check
        '''@app.route('/api/refund', methods=['POST'])
@require_role('finance')
@limiter.limit("10 per minute")
def {func_name}():
    order_id = request.json['order_id']
    amount = request.json['amount']
    if amount > MAX_REFUND_AMOUNT:
        abort(400, 'Amount exceeds limit')
    process_refund(order_id, amount, approved_by=current_user.id)
    return jsonify(refunded=True)'''
    ]
    
    samples = []
    for _ in range(50):
        template = random.choice(templates)
        code = template.format(
            id_var=random.choice(ID_VARS),
            func_name=random_func_name('admin_action')
        )
        samples.append(('Good', code, 'BrokenFuncAuth'))
    return samples


# =============================================================================
# OWASP API 6: Unrestricted Access to Sensitive Business Flows
# =============================================================================

def gen_business_flow_vulnerable():
    """Generate vulnerable samples - no business logic protection."""
    templates = [
        # No purchase limit
        '''@app.route('/api/purchase', methods=['POST'])
def {func_name}():
    product_id = request.json['product_id']
    quantity = request.json['quantity']
    # No limit on quantity - scalping vulnerability
    order = create_order(product_id, quantity, current_user.id)
    return jsonify(order_id=order.id)''',
        
        # Coupon reuse
        '''@app.route('/api/apply-coupon', methods=['POST'])
def {func_name}():
    coupon_code = request.json['code']
    coupon = Coupon.query.filter_by(code=coupon_code).first()
    if coupon:
        # No check if already used by this user
        apply_discount(current_user.cart_id, coupon.discount)
        return jsonify(success=True)
    return jsonify(error='Invalid coupon'), 400''',
        
        # No review limit
        '''@app.route('/api/review', methods=['POST'])
def {func_name}():
    product_id = request.json['product_id']
    rating = request.json['rating']
    # Can submit multiple reviews
    review = Review(product_id=product_id, rating=rating, user_id=current_user.id)
    db.session.add(review)
    db.session.commit()
    return jsonify(success=True)''',
        
        # No invitation limit
        '''@app.route('/api/invite', methods=['POST'])
def {func_name}():
    emails = request.json['emails']
    # No limit - can spam invitations
    for email in emails:
        send_invitation(email, current_user.referral_code)
    return jsonify(sent=len(emails))''',
        
        # Vote manipulation
        '''@app.route('/api/vote', methods=['POST'])
def {func_name}():
    poll_id = request.json['poll_id']
    choice = request.json['choice']
    # No duplicate vote check
    vote = Vote(poll_id=poll_id, choice=choice)
    db.session.add(vote)
    db.session.commit()
    return jsonify(success=True)'''
    ]
    
    samples = []
    for _ in range(50):
        template = random.choice(templates)
        code = template.format(func_name=random_func_name('business_flow'))
        samples.append(('Error', code, 'BusinessFlow'))
    return samples


def gen_business_flow_secure():
    """Generate secure samples - proper business logic protection."""
    templates = [
        # Purchase limit
        '''@app.route('/api/purchase', methods=['POST'])
@login_required
@limiter.limit("10 per hour")
def {func_name}():
    product_id = request.json['product_id']
    quantity = min(request.json['quantity'], MAX_QUANTITY_PER_ORDER)
    if get_user_purchases_today(current_user.id) >= DAILY_LIMIT:
        abort(429, 'Daily purchase limit exceeded')
    order = create_order(product_id, quantity, current_user.id)
    return jsonify(order_id=order.id)''',
        
        # Single-use coupon
        '''@app.route('/api/apply-coupon', methods=['POST'])
@login_required
def {func_name}():
    coupon_code = request.json['code']
    coupon = Coupon.query.filter_by(code=coupon_code).first()
    if not coupon or not coupon.is_valid():
        return jsonify(error='Invalid coupon'), 400
    if CouponUsage.query.filter_by(user_id=current_user.id, coupon_id=coupon.id).first():
        return jsonify(error='Coupon already used'), 400
    apply_discount(current_user.cart_id, coupon.discount)
    record_coupon_usage(current_user.id, coupon.id)
    return jsonify(success=True)''',
        
        # Single review per user
        '''@app.route('/api/review', methods=['POST'])
@login_required
@limiter.limit("5 per day")
def {func_name}():
    product_id = request.json['product_id']
    rating = request.json['rating']
    if Review.query.filter_by(product_id=product_id, user_id=current_user.id).first():
        return jsonify(error='Already reviewed'), 400
    if not has_purchased(current_user.id, product_id):
        return jsonify(error='Purchase required'), 403
    review = Review(product_id=product_id, rating=rating, user_id=current_user.id)
    db.session.add(review)
    db.session.commit()
    return jsonify(success=True)''',
        
        # Invitation limit
        '''@app.route('/api/invite', methods=['POST'])
@login_required
@limiter.limit("10 per day")
def {func_name}():
    emails = request.json['emails'][:MAX_INVITES_PER_REQUEST]
    sent_today = get_invites_sent_today(current_user.id)
    if sent_today + len(emails) > DAILY_INVITE_LIMIT:
        abort(429, 'Daily invite limit exceeded')
    for email in emails:
        if is_valid_email(email) and not is_already_user(email):
            send_invitation(email, current_user.referral_code)
    return jsonify(sent=len(emails))''',
        
        # Duplicate vote prevention
        '''@app.route('/api/vote', methods=['POST'])
@login_required
def {func_name}():
    poll_id = request.json['poll_id']
    choice = request.json['choice']
    if Vote.query.filter_by(poll_id=poll_id, user_id=current_user.id).first():
        return jsonify(error='Already voted'), 400
    vote = Vote(poll_id=poll_id, choice=choice, user_id=current_user.id)
    db.session.add(vote)
    db.session.commit()
    return jsonify(success=True)'''
    ]
    
    samples = []
    for _ in range(50):
        template = random.choice(templates)
        code = template.format(func_name=random_func_name('business_flow'))
        samples.append(('Good', code, 'BusinessFlow'))
    return samples


# =============================================================================
# OWASP API 7: Server Side Request Forgery (SSRF)
# =============================================================================

def gen_ssrf_vulnerable():
    """Generate SSRF vulnerable samples."""
    templates = [
        # Direct URL fetch
        '''@app.route('/api/fetch')
def {func_name}():
    {url_var} = request.args.get('url')
    response = requests.get({url_var})  # SSRF - can access internal resources!
    return jsonify(content=response.text)''',
        
        # Webhook without validation
        '''@app.route('/api/webhook', methods=['POST'])
def {func_name}():
    callback_url = request.json['callback_url']
    data = process_webhook()
    requests.post(callback_url, json=data)  # Can hit internal services
    return jsonify(success=True)''',
        
        # Image proxy
        '''@app.route('/proxy/image')
def {func_name}():
    image_url = request.args.get('src')
    img_data = urllib.request.urlopen(image_url).read()
    return Response(img_data, mimetype='image/png')''',
        
        # PDF generator with URL
        '''@app.route('/api/pdf/generate', methods=['POST'])
def {func_name}():
    html_url = request.json['template_url']
    html_content = requests.get(html_url).text  # Fetches any URL
    pdf = generate_pdf(html_content)
    return send_file(pdf)''',
        
        # URL preview
        '''@app.route('/api/preview')
def {func_name}():
    {url_var} = request.args.get('link')
    response = httpx.get({url_var}, follow_redirects=True)
    soup = BeautifulSoup(response.text, 'html.parser')
    return jsonify(title=soup.title.string if soup.title else '')'''
    ]
    
    samples = []
    for _ in range(50):
        template = random.choice(templates)
        code = template.format(
            url_var=random.choice(URL_VARS),
            func_name=random_func_name('fetch_url')
        )
        samples.append(('Error', code, 'SSRF'))
    return samples


def gen_ssrf_secure():
    """Generate SSRF secure samples."""
    templates = [
        # URL whitelist
        '''@app.route('/api/fetch')
@login_required
def {func_name}():
    {url_var} = request.args.get('url')
    parsed = urlparse({url_var})
    if parsed.netloc not in ALLOWED_DOMAINS:
        abort(400, 'Domain not allowed')
    if parsed.scheme not in ['http', 'https']:
        abort(400, 'Invalid scheme')
    response = requests.get({url_var}, timeout=5)
    return jsonify(content=response.text[:1000])''',
        
        # Webhook URL validation
        '''@app.route('/api/webhook', methods=['POST'])
@auth_required
def {func_name}():
    callback_url = request.json['callback_url']
    if not is_valid_webhook_url(callback_url):
        abort(400, 'Invalid callback URL')
    if is_internal_ip(urlparse(callback_url).hostname):
        abort(400, 'Internal IPs not allowed')
    data = process_webhook()
    requests.post(callback_url, json=data, timeout=10)
    return jsonify(success=True)''',
        
        # Image proxy with validation
        '''@app.route('/proxy/image')
@limiter.limit("100 per minute")
def {func_name}():
    image_url = request.args.get('src')
    parsed = urlparse(image_url)
    if not is_allowed_image_host(parsed.netloc):
        abort(403)
    if is_private_ip(socket.gethostbyname(parsed.hostname)):
        abort(403, 'Private IP not allowed')
    img_data = requests.get(image_url, timeout=5).content
    return Response(img_data, mimetype='image/png')''',
        
        # PDF with template ID (no URL)
        '''@app.route('/api/pdf/generate', methods=['POST'])
@login_required
def {func_name}():
    template_id = request.json['template_id']
    if template_id not in ALLOWED_TEMPLATES:
        abort(400, 'Invalid template')
    template_path = TEMPLATE_DIR / (template_id + ".html")
    with open(template_path) as f:
        html_content = f.read()
    pdf = generate_pdf(html_content)
    return send_file(pdf)''',
        
        # URL preview with DNS rebinding protection
        '''@app.route('/api/preview')
@limiter.limit("30 per minute")
def {func_name}():
    {url_var} = request.args.get('link')
    parsed = urlparse({url_var})
    resolved_ip = socket.gethostbyname(parsed.hostname)
    if ipaddress.ip_address(resolved_ip).is_private:
        abort(403, 'Private IP not allowed')
    response = httpx.get({url_var}, follow_redirects=False, timeout=5)
    soup = BeautifulSoup(response.text[:10000], 'html.parser')
    return jsonify(title=soup.title.string if soup.title else '')'''
    ]
    
    samples = []
    for _ in range(50):
        template = random.choice(templates)
        code = template.format(
            url_var=random.choice(URL_VARS),
            func_name=random_func_name('fetch_url')
        )
        samples.append(('Good', code, 'SSRF'))
    return samples


# =============================================================================
# OWASP API 8: Security Misconfiguration
# =============================================================================

def gen_misconfig_vulnerable():
    """Generate Security Misconfiguration vulnerable samples."""
    templates = [
        # Debug mode in production
        '''app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = 'dev-key-123'

@app.route('/')
def {func_name}():
    return 'Hello World\'''',
        
        # CORS allow all
        '''from flask_cors import CORS
app = Flask(__name__)
CORS(app, resources={{r"/*": {{"origins": "*"}}}})

@app.route('/api/data')
def {func_name}():
    return jsonify(sensitive_data())''',
        
        # Verbose error messages
        '''@app.errorhandler(Exception)
def {func_name}(e):
    return jsonify(
        error=str(e),
        traceback=traceback.format_exc(),
        config=str(app.config)  # Exposes configuration!
    ), 500''',
        
        # Default credentials
        '''DATABASE_CONFIG = {{
    'host': 'localhost',
    'user': 'root',
    'password': 'password',  # Default password!
    'database': 'production'
}}

@app.route('/api/users')
def {func_name}():
    return jsonify(get_users())''',
        
        # Exposed admin panel
        '''@app.route('/admin')
def {func_name}():
    # No authentication required!
    return render_template('admin.html', users=User.query.all())'''
    ]
    
    samples = []
    for _ in range(50):
        template = random.choice(templates)
        code = template.format(func_name=random_func_name('handle_request'))
        samples.append(('Error', code, 'Misconfiguration'))
    return samples


def gen_misconfig_secure():
    """Generate Security Misconfiguration secure samples."""
    templates = [
        # Production-safe config
        '''app = Flask(__name__)
app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', 'False') == 'True'
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True

@app.route('/')
def {func_name}():
    return 'Hello World\'''',
        
        # Restricted CORS
        '''from flask_cors import CORS
app = Flask(__name__)
CORS(app, resources={{
    r"/api/*": {{"origins": ALLOWED_ORIGINS, "methods": ["GET", "POST"]}}
}})

@app.route('/api/data')
@login_required
def {func_name}():
    return jsonify(get_user_data(current_user.id))''',
        
        # Safe error handling
        '''@app.errorhandler(Exception)
def {func_name}(e):
    app.logger.error(f"Error: {{e}}", exc_info=True)
    if app.debug:
        raise e
    return jsonify(error='An error occurred', request_id=request.id), 500''',
        
        # Secure database config
        '''DATABASE_CONFIG = {{
    'host': os.environ['DB_HOST'],
    'user': os.environ['DB_USER'],
    'password': os.environ['DB_PASSWORD'],
    'database': os.environ['DB_NAME'],
    'ssl': True
}}

@app.route('/api/users')
@admin_required
def {func_name}():
    return jsonify(get_users())''',
        
        # Protected admin panel
        '''@app.route('/admin')
@admin_required
@limiter.limit("30 per minute")
def {func_name}():
    audit_log('admin_access', current_user.id)
    return render_template('admin.html', users=User.query.all())'''
    ]
    
    samples = []
    for _ in range(50):
        template = random.choice(templates)
        code = template.format(func_name=random_func_name('handle_request'))
        samples.append(('Good', code, 'Misconfiguration'))
    return samples


# =============================================================================
# OWASP API 9: Improper Inventory Management
# =============================================================================

def gen_improper_inventory_vulnerable():
    """Generate Improper Inventory Management vulnerable samples."""
    templates = [
        # Exposed debug endpoint
        '''@app.route('/debug/info')
def {func_name}():
    return jsonify(
        version=app.config['VERSION'],
        routes=[str(r) for r in app.url_map.iter_rules()],
        database=DATABASE_URL
    )''',
        
        # Old API version still active
        '''@app.route('/api/v1/users')  # Deprecated but still works
def {func_name}():
    # Old version without authentication
    return jsonify([u.to_dict() for u in User.query.all()])

@app.route('/api/v2/users')
@jwt_required
def get_users_v2():
    return jsonify([u.to_dict() for u in User.query.all()])''',
        
        # Undocumented endpoint
        '''@app.route('/internal/metrics')
def {func_name}():
    # Not in API docs, no auth
    return jsonify(
        requests_per_minute=get_rpm(),
        active_sessions=len(sessions),
        db_pool_size=db.pool_size()
    )''',
        
        # Test endpoint in production
        '''@app.route('/test/create-admin')
def {func_name}():
    # Forgot to remove test endpoint!
    admin = User(username='testadmin', role='admin')
    db.session.add(admin)
    db.session.commit()
    return jsonify(id=admin.id)''',
        
        # Health check exposes info
        '''@app.route('/health')
def {func_name}():
    return jsonify(
        status='ok',
        database=db.engine.url,  # Exposes connection string!
        redis=redis.connection_pool.connection_kwargs
    )'''
    ]
    
    samples = []
    for _ in range(50):
        template = random.choice(templates)
        code = template.format(func_name=random_func_name('internal_endpoint'))
        samples.append(('Error', code, 'ImproperInventory'))
    return samples


def gen_proper_inventory_secure():
    """Generate Proper Inventory Management secure samples."""
    templates = [
        # No debug in production
        '''@app.route('/debug/info')
@admin_required
def {func_name}():
    if not app.debug:
        abort(404)
    return jsonify(version=app.config['VERSION'])''',
        
        # Deprecated API redirects
        '''@app.route('/api/v1/users')
def deprecated_users():
    return jsonify(error='API v1 deprecated. Use /api/v2/users'), 410

@app.route('/api/v2/users')
@jwt_required
def {func_name}():
    return jsonify([u.to_dict() for u in User.query.all()])''',
        
        # Internal metrics protected
        '''@app.route('/internal/metrics')
@require_internal_network
@admin_required
def {func_name}():
    return jsonify(
        requests_per_minute=get_rpm(),
        active_sessions=count_active_sessions(),
        status='healthy'
    )''',
        
        # No test endpoints in prod
        '''if os.environ.get('FLASK_ENV') == 'development':
    @app.route('/test/create-admin')
    def create_test_admin():
        admin = User(username='testadmin', role='admin')
        db.session.add(admin)
        db.session.commit()
        return jsonify(id=admin.id)

@app.route('/api/status')
def {func_name}():
    return jsonify(status='running')''',
        
        # Safe health check
        '''@app.route('/health')
def {func_name}():
    try:
        db.session.execute('SELECT 1')
        db_status = 'ok'
    except:
        db_status = 'error'
    return jsonify(status='ok', database=db_status)'''
    ]
    
    samples = []
    for _ in range(50):
        template = random.choice(templates)
        code = template.format(func_name=random_func_name('internal_endpoint'))
        samples.append(('Good', code, 'ImproperInventory'))
    return samples


# =============================================================================
# OWASP API 10: Unsafe Consumption of APIs
# =============================================================================

def gen_unsafe_api_consumption_vulnerable():
    """Generate Unsafe Consumption of APIs vulnerable samples."""
    templates = [
        # No response validation
        '''@app.route('/api/user-info/<user_id>')
def {func_name}(user_id):
    response = requests.get(f"{{EXTERNAL_API}}/users/{{user_id}}")
    # Trusting external API response without validation!
    user_data = response.json()
    update_local_user(user_id, user_data)
    return jsonify(user_data)''',
        
        # No SSL verification
        '''@app.route('/api/payment')
def {func_name}():
    payment_data = request.json
    response = requests.post(
        PAYMENT_API_URL,
        json=payment_data,
        verify=False  # SSL verification disabled!
    )
    return jsonify(response.json())''',
        
        # Blindly trusting redirects
        '''@app.route('/api/fetch-external')
def {func_name}():
    {url_var} = request.args.get('url')
    response = requests.get({url_var}, allow_redirects=True)  # Follows any redirect
    return jsonify(data=response.json())''',
        
        # No timeout
        '''@app.route('/api/third-party')
def {func_name}():
    response = requests.get(THIRD_PARTY_API)  # No timeout - can hang forever
    if response.status_code == 200:
        return jsonify(response.json())
    return jsonify(error='Failed'), 500''',
        
        # No error handling for external API
        '''@app.route('/api/enrich')
def {func_name}():
    data = request.json
    enriched = requests.post(ENRICHMENT_API, json=data).json()
    # No validation of enriched data
    db.execute(f"UPDATE users SET data = '{{enriched}}'")
    return jsonify(success=True)'''
    ]
    
    samples = []
    for _ in range(50):
        template = random.choice(templates)
        code = template.format(
            url_var=random.choice(URL_VARS),
            func_name=random_func_name('consume_api')
        )
        samples.append(('Error', code, 'UnsafeAPIConsumption'))
    return samples


def gen_safe_api_consumption_secure():
    """Generate Safe Consumption of APIs secure samples."""
    templates = [
        # Response validation
        '''@app.route('/api/user-info/<user_id>')
@login_required
def {func_name}(user_id):
    response = requests.get(f"{{EXTERNAL_API}}/users/{{user_id}}", timeout=10)
    if response.status_code != 200:
        abort(502)
    user_data = response.json()
    schema = ExternalUserSchema()
    validated = schema.load(user_data)  # Validate external data
    update_local_user(user_id, validated)
    return jsonify(validated)''',
        
        # SSL verification enabled
        '''@app.route('/api/payment')
@login_required
def {func_name}():
    payment_data = PaymentSchema().load(request.json)
    response = requests.post(
        PAYMENT_API_URL,
        json=payment_data,
        verify=True,
        cert=CLIENT_CERT,
        timeout=30
    )
    if response.status_code != 200:
        audit_log('payment_failed', current_user.id)
        abort(502)
    return jsonify(PaymentResponseSchema().load(response.json()))''',
        
        # Redirect control
        '''@app.route('/api/fetch-external')
@limiter.limit("10 per minute")
def {func_name}():
    {url_var} = request.args.get('url')
    if not is_allowed_domain({url_var}):
        abort(400)
    response = requests.get({url_var}, allow_redirects=False, timeout=5)
    if response.is_redirect:
        abort(400, 'Redirects not allowed')
    return jsonify(data=response.json())''',
        
        # Proper timeout and retry
        '''@app.route('/api/third-party')
@limiter.limit("30 per minute")
def {func_name}():
    try:
        response = requests.get(THIRD_PARTY_API, timeout=10)
        response.raise_for_status()
        return jsonify(ThirdPartySchema().load(response.json()))
    except requests.Timeout:
        return jsonify(error='Service timeout'), 504
    except requests.RequestException as e:
        app.logger.error(f"Third party API error: {{e}}")
        return jsonify(error='Service unavailable'), 503''',
        
        # Safe data handling
        '''@app.route('/api/enrich')
@login_required
def {func_name}():
    data = EnrichRequestSchema().load(request.json)
    try:
        response = requests.post(ENRICHMENT_API, json=data, timeout=15)
        enriched = EnrichResponseSchema().load(response.json())
        sanitized = sanitize_for_db(enriched)
        db.execute("UPDATE users SET data = :data WHERE id = :id",
                   {{"data": json.dumps(sanitized), "id": current_user.id}})
        return jsonify(success=True)
    except ValidationError as e:
        return jsonify(error='Invalid response from enrichment API'), 502'''
    ]
    
    samples = []
    for _ in range(50):
        template = random.choice(templates)
        code = template.format(
            url_var=random.choice(URL_VARS),
            func_name=random_func_name('consume_api')
        )
        samples.append(('Good', code, 'UnsafeAPIConsumption'))
    return samples


# =============================================================================
# Main Generator
# =============================================================================

def generate_dataset():
    """Generate the complete OWASP dataset."""
    print("="*60)
    print(" OWASP Top 10 API Vulnerability Dataset Generator")
    print("="*60)
    
    all_samples = []
    
    # Generate for each OWASP category
    generators = [
        ("API1: BOLA", gen_bola_vulnerable, gen_bola_secure),
        ("API2: Broken Auth", gen_broken_auth_vulnerable, gen_broken_auth_secure),
        ("API3: Mass Assignment", gen_mass_assignment_vulnerable, gen_mass_assignment_secure),
        ("API4: No Rate Limiting", gen_no_rate_limit_vulnerable, gen_rate_limit_secure),
        ("API5: Broken Func Auth", gen_broken_func_auth_vulnerable, gen_func_auth_secure),
        ("API6: Business Flow", gen_business_flow_vulnerable, gen_business_flow_secure),
        ("API7: SSRF", gen_ssrf_vulnerable, gen_ssrf_secure),
        ("API8: Misconfiguration", gen_misconfig_vulnerable, gen_misconfig_secure),
        ("API9: Improper Inventory", gen_improper_inventory_vulnerable, gen_proper_inventory_secure),
        ("API10: Unsafe API Consumption", gen_unsafe_api_consumption_vulnerable, gen_safe_api_consumption_secure),
    ]
    
    for name, vuln_gen, secure_gen in generators:
        vuln_samples = vuln_gen()
        secure_samples = secure_gen()
        all_samples.extend(vuln_samples)
        all_samples.extend(secure_samples)
        print(f"  {name}: {len(vuln_samples)} vulnerable + {len(secure_samples)} secure")
    
    # Shuffle
    random.shuffle(all_samples)
    
    # Save to CSV
    output_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(output_dir, 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    output_path = os.path.join(data_dir, 'owasp_expanded_dataset.csv')
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Result', 'Code', 'vulnerability_type'])
        for result, code, vuln_type in all_samples:
            writer.writerow([result, code, vuln_type])
    
    print(f"\n{'='*60}")
    print(f" Dataset Generated!")
    print(f"{'='*60}")
    print(f"  Total samples: {len(all_samples)}")
    print(f"  Vulnerable: {sum(1 for r,_,_ in all_samples if r == 'Error')}")
    print(f"  Secure: {sum(1 for r,_,_ in all_samples if r == 'Good')}")
    print(f"  Saved to: {output_path}")
    print(f"{'='*60}")
    
    return output_path


if __name__ == "__main__":
    generate_dataset()
