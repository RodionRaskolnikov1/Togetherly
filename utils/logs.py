from models.user_logs import UserLogs, AdminLogs, SuperAdminLogs, CoordinatorLogs


def create_user_log(db, user_id, action, ip=None, user_agent=None):
    
    try:
        log = UserLogs(
            user_id=user_id,
            action=action,
            ip_address=ip,
            user_agent=user_agent
        )   
        db.add(log)
        db.commit()
    except Exception as e:
        db.rollback()
        print(e)
        pass

def create_admin_log(db, admin_id, action, ip=None, user_agent=None):
    
    try:
        log = AdminLogs(
            admin_id=admin_id,
            action=action,
            ip_address=ip,
            user_agent=user_agent
        )   
        db.add(log)
        db.commit()
    except Exception as e:
        db.rollback()
        print(e)
        pass

def create_coordinator_log(db, coordinator_id, action, ip=None, user_agent=None):
    
    try:
        log = CoordinatorLogs(
            coordinator_id=coordinator_id,
            action=action,
            ip_address=ip,
            user_agent=user_agent
        )   
        db.add(log)
        db.commit()
    except Exception as e:
        db.rollback()
        print(e)
        pass
    
    
def create_super_admin_log(db, super_admin_id, action, ip=None, user_agent=None):
    
    try:
        log = SuperAdminLogs(
            super_admin_id=super_admin_id,
            action=action,
            ip_address=ip,
            user_agent=user_agent
        )   
        db.add(log)
        db.commit()
    except Exception as e:
        db.rollback()
        print(e)
        pass